import os
import random
import time
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager


class JiuYinDriver:

    def __init__(self, sin_out, work_status, error_pic_path=None):

        self.sin_out = sin_out
        self.work_status = work_status

        self.error_pic_path = error_pic_path
        self.driver = None

    def get_driver(self):

        self.sin_out.emit("开始下载Edge浏览器驱动(8M)，需要亿点点时间")

        user_agent: str = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.24(0x1800182c) NetType/WIFI Language/zh_CN"

        options = Options()
        mobile_emulation = {'deviceName': 'iPhone 8'}
        options.add_argument('user-agent=%s' % user_agent)
        options.add_experimental_option('mobileEmulation', mobile_emulation)

        pref = {
            # 不显示图片
            'profile.default_content_setting_values': {
                'images': 2
            }
        }
        options.add_experimental_option('prefs', pref)
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--disable-gpu')
        try:
            self.driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent, "platform": "iphone"})
            self.sin_out.emit("Edge浏览器环境准备检查完毕")
            return True
        except Exception as e:
            self.sin_out.emit("Edge浏览器与驱动文件不一致，请确认Edge浏览器版本信息或联系作者")
            return False

    def get_windows_img(self):
        """
        在这里把file_path这个参数写死，直接保存到项目的一个文件夹../screenshots/下
        """
        file_path = os.path.dirname(os.path.abspath('../../../')) if self.error_pic_path is None else self.error_pic_path
        rq = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
        screen_name = file_path + '/JiuYinErrorPic/' + rq + '.png'
        self.driver.get_screenshot_as_file(screen_name)

    def open_url(self) -> bool:
        """
        打开yrl
        :return:
        """
        if self.driver is not None:
            try:
                self.driver.get(url="https://9yin.woniu.com/m/static/act/202205/siginIn/")
                self.sin_out.emit("正在打开签到页面")
                return True
            except Exception as e:
                self.sin_out.emit("无法访问签到页面，请检查网络")
                self.sin_out.emit("签到页面为： https://9yin.woniu.com/m/static/act/202205/siginIn/")
                return False
        else:
            return False

    def find_elements(self, by: By, value: str) -> list[WebElement]:
        """
        查找元素合集
        :param by:
        :param value:
        :return:
        """
        ele = self.wait_element(by=by, value=value)
        if ele is not None:
            elements = self.driver.find_elements(by=by, value=value)
            return elements

    def wait_element(self, by: By, value: str, wait_type: str = 'visibility', wait_time: int = 10) -> bool or Exception:
        """
        显性等待
        :param by: By.ID
        :param value: 元素值
        :param wait_time: 等待时间，默认10秒
        :param wait_type: 元素应该处于什么状态
        等待的类型 ：
        存在   presence
        显示   visibility
        不显示但存在 invisibility
        可点击 click
        已选择 selected
        :return: 返回True或者False
        """
        locator = (by, value)
        try:
            if WebDriverWait(self.driver, wait_time, 2).until(ec.presence_of_element_located(locator)):
                if wait_type == 'visibility':
                    WebDriverWait(self.driver, wait_time, 2).until(ec.visibility_of_element_located(locator))
                    return True
                elif wait_type == 'click':
                    WebDriverWait(self.driver, wait_time, 2).until(ec.element_to_be_clickable(locator))
                    return True
        except Exception:
            return False

    def wait_alert(self):
        try:
            WebDriverWait(self.driver, 5, 0.5).until(ec.alert_is_present())
            return True
        except Exception as e:
            # self.get_windows_img()
            return False

    def click(self, by: By, value: str):
        """
        点击元素
        :param by: By.ID
        :param value: By对应的类型值
        :return:
        """
        if self.wait_element(by, wait_type='click', value=value) is True:
            self.driver.find_element(by, value).click()

    def click_by_js(self, selector: str, index=None):
        """
        使用JS的方法来点击元素
        :param index: 需要查找第几个元素
        :param selector: js_class_name
        :return:
        """
        selector_by = selector.split('=>')[0]
        selector_value = selector.split('=>')[1]
        element = None
        if selector_by == 'js_class_name':
            if index is not None:
                # 取第一个找到的元素
                element = 'document.querySelectorAll(".' + selector_value + '")[' + str(index) + ']'
            else:
                element = 'document.querySelectorAll(".' + selector_value + '")[0]'  # 取第一个找到的元素
        js = element + '.click()'
        try:
            self.driver.execute_script(js)
            return True
        except Exception as e:
            return e

    def send_key(self, by: By, value: str, text: str):
        """
        在文本框输入内容
        :param by: 元素类型
        :param value: 元素值
        :param text: 输入的文本
        :return:
        """
        if self.wait_element(by, value=value) is True:
            el = self.driver.find_element(by=by, value=value)
            el.clear()
            el.send_keys(text)

    def quit(self):
        self.driver.quit()

    def close_result_tips(self) -> str or Exception:
        """
        关闭弹窗提示，成功或者失败的
        :return:
        """
        if self.wait_alert():
            self.driver.switch_to.alert.accept()
            self.sin_out.emit("今日已经签到过，请勿重复签到")
        else:
            self.click(By.XPATH, "//div[@class='model_x']")
            data_list = self.find_elements(By.CSS_SELECTOR, ".black.black1")
            self.sin_out.emit("签到成功，当前签到数为 %s 天，请明天再来哦" % str(len(data_list)))


class business(JiuYinDriver):

    def __init__(self, sin_out, work_status, error_pic_path):
        super().__init__(sin_out, work_status, error_pic_path)

    def get_url(self) -> bool:
        return self.open_url()

    def login(self, account: str, password: str):
        self.click(By.ID, "login")
        self.send_key(By.ID, "logUsername", account)
        self.send_key(By.ID, "logPassword", password)
        self.click(By.ID, "loginBtn")
        self.sin_out.emit("账号(%s)正在登录..." % account)
        return self.wait_element(By.XPATH, "//div[@class='logout']/a")

    def login_out(self):
        self.sin_out.emit("当前账号退出登录，避免速度过快被蜗牛拦截，开始随机等待10-30秒，请稍后")
        self.click(By.XPATH, "//div[@class='logout']/a")
        sleep(random.randint(10, 20))
        self.driver.refresh()
        sleep(random.randint(5, 10))

    def select_area(self, area, service):
        self.sin_out.emit("开始选择服务器（%s）" % service)
        sleep(1)
        self.click(By.XPATH, "//div[@class='select_box']//div[@class='select' and text()='请选择游戏分区']")
        if not self.wait_element(By.XPATH, "//ul[@class='select_ul']/li[text()='%s']" % area):
            self.sin_out.emit("游戏大区（%s）信息不正确，请重新检查" % area)
            return False
        try:
            self.driver.execute_script("arguments[0].scrollIntoView()", self.driver.find_element(By.XPATH, "//ul[@class='select_ul']/li[text()='%s']" % area))
            self.click(By.XPATH, "//ul[@class='select_ul']/li[text()='%s']" % area)
            sleep(1)

            self.click(By.XPATH, "//div[@class='select_box']//div[@class='select1' and text()='请选择分区服务器']")
            if not self.wait_element(By.XPATH, "//ul[@class='select_ul1']/li[text()='%s']" % service):
                self.sin_out.emit("游戏服务器（%s）信息不正确，请重新检查" % service)
                return False
            self.click(By.XPATH, "//ul[@class='select_ul1']/li[text()='%s']" % service)
            sleep(2)
        except Exception as e:
            self.sin_out.emit(e)
            return False
        return True

    def sign_wechat(self):
        data_list = self.find_elements(By.CSS_SELECTOR, ".black.black1")  # 已经签到了几天
        self.sin_out.emit("开始检查签到状态，已签到 %s 天" % str(len(data_list)))
        data_list = [] if data_list is None else data_list
        if len(data_list) > 0:
            # 说明已经有签到记录了
            data_list_all = self.find_elements(By.XPATH,
                                               "//div[@class='siginIn_box']/div[@class='item_box']")  # 这个月有多少天
            if len(data_list) < len(data_list_all):
                # 如果签到天数小于当月天数
                self.click_by_js(selector="js_class_name=>box_bottom", index=len(data_list))
        else:
            # 说明还没签到过
            self.click_by_js(selector="js_class_name=>box_bottom", index=0)
        self.close_result_tips()