#!/usr/bin/env python
# coding=utf-8
# Python3
"""
@Dept  : 云计算安全研发中心
@Author: liuhaojie
@File  : train.py
@Idea  : IntelliJ IDEA
@Date  : 2020/7/16
@Desc  : Descriptions
"""
import logging
import optparse
import os
import time
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from sklearn import metrics
from sklearn.externals import joblib
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier

logging.basicConfig(level=logging.DEBUG,
                    filename='log/trainlog.log',
                    filemode='a',
                    format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


def model_collection(mode):
    if mode == 'mlp':
        return MLPClassifier(solver="lbfgs", alpha=1e-5, hidden_layer_sizes=(5, 2), random_state=1)
    if mode == 'xgb':
        return XGBClassifier()
    if mode == 'gnb':
        return GaussianNB()


def read_file(filename):
    text = b""
    with open(filename, "rb") as f:
        for line in f:
            line = line.strip(b"\r\t")
            text += line
    return text


def read_dir(path):
    text_list = []
    for r, d, files in os.walk(path):
        for file in files:
            filename = r + "/" + file
            if os.path.splitext(file)[-1].lower() in filetypes:
                text = read_file(filename)
                text_list.append(text)
    return text_list


def features_process(negativedir, postivedir, maxfeatures):
    webshell_texts = read_dir(negativedir)
    normal_texts = read_dir(postivedir)
    webshell_number = len(webshell_texts)
    normal_number = len(normal_texts)
    texts = webshell_texts + normal_texts
    webshell_lables = [1] * webshell_number
    normal_lables = [0] * normal_number
    lables = webshell_lables + normal_lables
    logger.info("白样本总量：%i" % normal_number)
    logger.info("黑样本总量：%i" % webshell_number)

    countvectorizer = CountVectorizer(ngram_range=(2, 2), decode_error="ignore",
                                      min_df=1, analyzer="word",
                                      token_pattern=r'[^\w\s]+|\b\w+\b',
                                      max_features=maxfeatures)
    tfidftransformer = TfidfTransformer(smooth_idf=False)
    cv_x = countvectorizer.fit_transform(texts).toarray()
    tf_x = tfidftransformer.fit_transform(cv_x).toarray()

    joblib.dump(countvectorizer, "model/countvectorizer_" + options.version + ".pkl")
    joblib.dump(tfidftransformer, "model/tfidftransformer_" + options.version + ".pkl")
    return tf_x, lables, countvectorizer, tfidftransformer


def plot_roc(x_test, y_test, clf):
    """
    当模型为mlp时进行roc
    :param x_test:
    :param y_test:
    :param clf:
    :return:
    """
    if options.mode == 'mlp':
        y_test_score = clf.predict_proba(x_test)[:, 1]
        # y_pred = clf.predict(x_test)
        fpr, tpr, threshold = roc_curve(y_test, y_test_score)
        roc_auc = auc(fpr, tpr)
        lw = 2
        plt.figure(figsize=(7, 7))
        plt.plot(fpr, tpr, color='darkorange',
                 lw=lw, label='webshellDc (AUC = %0.5f)' % roc_auc)  ###横坐标为假正率，纵坐标为真正率
        plt.plot([0, 1], [0, 1], color='navy', lw=lw, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver operating characteristic curve')
        plt.legend(loc="lower right")
        plt.show()
    else:
        pass


def evaluation(y_test, y_pred):
    logger.info("准确率:%s" % metrics.accuracy_score(y_test, y_pred))
    logger.info(confusion_matrix(y_test, y_pred))
    logger.info(classification_report(y_test, y_pred))


def train(trainset, lables, mode, seed):
    x_train, x_test, y_train, y_test = train_test_split(trainset, lables, test_size=0.3, random_state=seed)
    clf = model_collection(mode)
    clfname = "model/" + mode + "_" + options.version + ".pkl"
    clf.fit(x_train, y_train)
    # logger.info("训练集评估：")
    # evaluation(y_train, clf.predict(x_train))
    logger.info("测试集评估：")
    evaluation(y_test, clf.predict(x_test))
    joblib.dump(clf, clfname, compress=3)
    plot_roc(x_test, y_test, clf)


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-v", "--version", dest="version", default="v0", help=u'当前训练版本号')
    parser.add_option("-s", "--seed", dest="seed", default=777, type="int", help=u'模型训练随机种子')
    parser.add_option("-p", "--postive_dir", dest="normal", default=False, help=u'训练白样本文件夹路径')
    parser.add_option("-n", "--negative_dir", dest="webshell", default=False, help=u'训练黑样本文件夹路径')
    parser.add_option("-m", "--model", dest="mode", default="mlp", help=u'训责训练的模型种类')
    parser.add_option("-d", "--dimensions", dest="max_features", default=25000, type="int", help=u'特征向量维度')
    options, _ = parser.parse_args()
    filetypes = ['.php', '.jsp', '.asp', '.aspx', '.jspx', '.java', '.txt']
    logger.info("初始化参数：")
    logger.info("当前训练版本号：%s" % options.version)
    logger.info("白样本路径：%s" % options.normal)
    logger.info("黑样本路径：%s" % options.webshell)
    logger.info("训练模型：%s" % options.mode)
    logger.info("随机种子：%s" % options.seed)
    logger.info("特征维度：%s" % options.max_features)
    sTime = time.time()
    x, y, cv, transformer = features_process(options.webshell, options.normal, options.max_features)
    train(x, y, options.mode, options.seed)
    eTime = time.time()
    logger.info("训练耗时：%s" % str(eTime - sTime))

# /Users/hadoop/Jupyter/恶意代码/webshell/dataset/
