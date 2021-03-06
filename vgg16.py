#!/usr/bin/python
# -*- coding: utf-8 -*-
# https://blog.keras.io/building-powerful-image-classification-models-using-very-little-data.html : 数据集太小的方法

# Using the bottleneck features of a pre-trained network VGG16
# Method: 1. train the classification model based on VGG16: a pre-trained keras model
#         2. use all the training data
# score:2.多
import pandas as pd
import numpy as np
from os import listdir
from tqdm import tqdm
from keras.applications import vgg16
from keras.preprocessing import image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, accuracy_score


data_dir = './data/'
SEED = 1987


def read_img(img_id, train_or_test, size):
    img = image.load_img(data_dir+train_or_test+"/"+str(img_id)+".jpg", target_size=size)
    img_pixels = image.img_to_array(img)
    return img_pixels


def main():
    labels = pd.read_csv(data_dir+'labels.csv')
    num_classes = len(labels.groupby('breed'))
    selected_labels = labels.groupby('breed').count().sort_values(by='id',ascending=False).head(num_classes).index.values

    labels = labels[labels['breed'].isin(selected_labels)]
    labels['target'] = 1
    labels['rank'] = labels.groupby('breed').rank()['id']
    labels_pivot = labels.pivot('id', 'breed', 'target').reset_index().fillna(0) # values必须是breed和target对应的值
    np.random.seed(SEED)
    y_train = labels_pivot[selected_labels].values
    ytr = y_train

    INPUT_SIZE = 224
    POOLING = 'avg'
    x_train = np.zeros((len(labels), INPUT_SIZE, INPUT_SIZE, 3), dtype='float32')
    for i, img_id in tqdm(enumerate(labels['id'])):
        # print i, img_id
        img = read_img(img_id, 'train', (INPUT_SIZE,INPUT_SIZE))
        x = vgg16.preprocess_input(np.expand_dims(img.copy(), axis=0))
        x_train[i] = x
    print('Train Images shape: {} size: {:,}'.format(x_train.shape, x_train.size))

    num_tests = len(listdir(data_dir + '/test/'))
    x_test = np.zeros((num_tests,INPUT_SIZE, INPUT_SIZE, 3), dtype='float32')
    test_id = []
    for i in range(num_tests):
        img_file_name = listdir(data_dir + '/test/')[i]
        img_id = img_file_name[0:len(img_file_name)-4]
        img = read_img(img_id, 'test',(INPUT_SIZE,INPUT_SIZE))
        x = vgg16.preprocess_input(np.expand_dims(img.copy(), axis=0))
        x_test[i] = x
        test_id.append(img_id)

    xtr = x_train

    vgg_bottleneck = vgg16.VGG16(weights='imagenet', include_top=False, pooling=POOLING)
    train_vgg_bf = vgg_bottleneck.predict(xtr, batch_size=32, verbose=1)
    valid_vgg_bf = vgg_bottleneck.predict(x_test, batch_size=32, verbose=1)
    logreg = LogisticRegression(multi_class='multinomial', solver='lbfgs', random_state=SEED)
    logreg.fit(train_vgg_bf, (ytr * range(num_classes)).sum(axis=1))
    valid_probs = logreg.predict_proba(valid_vgg_bf)

    # without formatting
    df1 = {'id': test_id}
    res1 = pd.DataFrame(data=df1)
    res2 = pd.DataFrame(columns=selected_labels, data=valid_probs)
    res = pd.concat([res1, res2], axis=1)
    res.to_csv("./vgg.csv", index=False)

    # format as the sample submission
    sample_submission = pd.read_csv(data_dir + 'sample_submission.csv')
    sample_ids = list(sample_submission['id'])
    sample_breeds = list(sample_submission.columns.values)[1:]
    reorder_df = res.set_index('id')
    reorder_df = reorder_df.loc[sample_ids].reset_index().reindex(columns=['id'] + sample_breeds)
    reorder_df.to_csv("./vgg_submit.csv", index=False)


if __name__ == '__main__':
    main()
"""
检查pixels是否normalized
总结防止overfitting的方法（数据集小的时候）：dropout，data augmentation, l1 and l2 regularization抗干扰能力强：https://blog.csdn.net/u012162613/article/details/44261657
"""