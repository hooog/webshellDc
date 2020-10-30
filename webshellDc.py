#!/usr/bin/env python
# coding=utf-8
# Python3
"""
@Dept  : 云计算安全研发中心
@Author: liuhaojie
@File  : webshellDc.py
@Idea  : IntelliJ IDEA
@Date  : 2020/7/15
@Desc  : Descriptions
"""
import logging
import os
import numpy as np

from sklearn.externals import joblib

logging.basicConfig(level=logging.DEBUG,
                    filename='log/checklog.log',
                    filemode='a',
                    format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


class WebshellDec(object):
    def __init__(self, vs):
        super(WebshellDec, self).__init__()
        self.cv = joblib.load("model/countvectorizer_" + vs + ".pkl")
        self.transformer = joblib.load("model/tfidftransformer_" + vs + ".pkl")
        self.mlp = joblib.load("model/mlp_" + vs + ".pkl")

    @staticmethod
    def load_file(file_path):
        t = b''
        with open(file_path, "rb") as f:
            for line in f:
                line = line.strip(b'\r\t')
                t += line
        return t

    def checkdir(self, path):
        counter, webshell_number, normal_number = 0, 0, 0
        for r, d, files in os.walk(path):
            for file in files:
                file_path = r + '/' + file
                if os.path.splitext(file)[-1].lower() in ['.php', '.jsp', '.jspx', '.java', '.asp', '.aspx']:
                    t = self.load_file(file_path)
                    t_list = list()
                    t_list.append(t)
                    x = self.cv.transform(t_list).toarray()
                    x = self.transformer.transform(x).toarray()
                    y_pred = self.mlp.predict(x)
                    counter += 1
                    if y_pred[0] == 1:
                        logger.info("{} is webshell".format(file_path))
                        webshell_number += 1
                    else:
                        logger.info("{} is not webshell".format(file_path))
                        normal_number += 1
        logger.info("检测总量:%i, 检测出webshell:%i, 检测出正常文件:%i" % (counter, webshell_number, normal_number))

    def check(self, input_data):
        if os.path.isdir(input_data):
            return self.checkdir(input_data)
        elif os.path.isfile(input_data):
            t = [self.load_file(input_data)]
            x = self.cv.transform(t).toarray()
            x = self.transformer.transform(x).toarray()
            y_pred = self.mlp.predict(x)[0]
            logger.info("输入文件：%s" % input_data)
            logger.info("检测结果：%s" % "webshell" if y_pred == 1 else "正常文件")
        else:
            if type(input_data) is bytes or type(input_data) is str:
                try:
                    t = [input_data.decode()]
                except AttributeError:
                    t = [input_data]
                x = self.cv.transform(t).toarray()
                x = self.transformer.transform(x).toarray()
                y_pred = self.mlp.predict(x)
                logger.info("输入代码：%s" % input_data)
                logger.info("检测结果：%s" % "webshell" if y_pred == 1 else "正常代码")
            else:
                logger.info("输入无效")


if __name__ == "__main__":
    assert (np.__version__ >= "1.18.5")
    logger.info("输入模型版本号...")
    while True:
        try:
            version = input("version:")
            logger.info("初始化模型...")
            webshelldc = WebshellDec(version)
            logger.info("初始化模型完成，输入检测内容，支持脚本文件、文本代码、文件路径")
            break
        except FileNotFoundError:
            logger.info("对应版本模型不存在，请重新输入模型版本号...")

    while True:
        inputs = input("inputs:")
        if inputs == "exit":
            logger.info("退出检测！")
            break
        else:
            webshelldc.check(inputs)
            logger.info("继续输入：")
# text = '<?php@eval($_GET[\'p\'])\n<?php assert (    $_GET[\'p\']\n)\n$func="test";$b374k=$func(\'$x\', \'ev\'.\'al\')\n$b=$W(\'\',$S);$b();\n;$pouet($pif,$paf);\n${$pouet}\n\'pouet\'.\'pif\' . \'pouet\' . "lol" ."kwainkwain"\n'
# print(webshelldc.check(text))
