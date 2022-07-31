# import cv2
# from numpy import zeros, uint8
#
#
# def imgContoursROI():
#     """使用查找到的轮廓生成ROI剪切图片中感兴趣区域"""
#     img = cv2.imread('D:/9.png')  # 载入图像
#     img = img[759:799, 759:1180]
#     #cv2.imshow("resources", img)
#     copyImg = img.copy()  # 原图像的拷贝
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     ret, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)  # 阈值化
#     contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  # 寻找轮廓线
#     mask = zeros(img.shape, uint8)  # 原图大小的纯黑mask图像
#     draw = zeros(img.shape, uint8)  # 将原图 copyTo 到draw上,加上mask操作
#     temp = zeros(img.shape, uint8)  # 每次循环，重置mask 和 draw
#     i = 0
#     for contour in contours:  # 遍历所有轮廓
#         area = cv2.contourArea(contour)  # 轮廓图面积
#         B = 255
#         G = 255
#         R = 255  # 生成颜色
#         mask = temp.copy()
#         draw = temp.copy()
#         if (area > 300):  # 轮廓面积大于300的做 mask
#             cv2.drawContours(mask, [contour], -1, (B, G, R), cv2.FILLED)
#
#             ROIname = 'ROI{num}'.format(num=i)
#             ROI = cv2.bitwise_and(img, mask)  # 图形与mask 的 and 运算
#             cv2.imshow(ROIname, ROI)
#             i += 1
#     cv2.waitKey(0)
#
#
# if __name__ == '__main__':
#     imgContoursROI()
#
#
#
