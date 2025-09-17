
# <div align='center'>九阴真经OL摸鱼小助手</div> 

<div align=center>
<img src="https://github.com/moonlessdark/JiuYinDance/blob/master/Resources/Readme/cover.png">
</div>

## 特别提示:
----  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;如果该脚本被微软的杀毒软件(Windows Defender)报毒，请按照  **[此教程](https://segmentfault.com/q/1010000039054120/a-1020000039066088)** 或者 **[此打包方法](https://blog.csdn.net/gitblog_07610/article/details/148467320)** 给出的方案处理。
报毒是打包工具Pyinstaller引起的。  
  
## 欢迎语：
----  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;欢迎各位大佬来 **侠骨丹心** 游玩，峨眉山上风景好，泉水甜，师姐师妹们各个都是人才，说话又好听...  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;如果觉得脚本有帮助到你，可以在游戏中给我邮2个馒头*´∀`)´∀`)*´∀`)*´∀`) ...  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;当前版本为重构版，调整了项目结构，优化的识别逻辑，精简了一些无用的功能，并调整了一下程序界面，提升了程序的稳定性(理论上)...  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;脚本不定时更新，会根据我在游戏中的实际情况添加或者优化功能，此脚本只会做一些自己会长期用到的能减负的小功能...  

## 前言:
----  

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;本项目是用于学习opencv与PySide6的实操作品，仅供学习。免费作品,请勿用于商业。   
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;此脚本支持的功能较少，且不算稳定，抗干扰性较差，只适合在老区养老，不适合新区养号。  

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;若您需要更多的功能，建议参考以下2种收费的脚本:  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- 麦卡Mac助手，可以在淘宝购买。  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- **[PC助手·九阴全系列解决方案 官网](https://www.ookan.com/)**  

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;本脚本在win10系统开发，其他系统未做兼容和调试，不保证能正常使用。  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;此脚本为“图色脚本”，不支持窗口绑定，不支持窗口最小化。  

## 系统硬件与设置  
----  
### 硬件  

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;22年6月蜗牛更新之后，免费版大漠插件只能在win7系统使用，此脚本改为使用“幽灵键鼠”(一个小U盘)。  
<div align=center><img src="https://github.com/moonlessdark/JiuYinDance/blob/master/Resources/Readme/ghostkb.PNG" style="width:20%; height:auto;"></div>
<div align=center>“幽灵键鼠”请在淘宝购买，买最便宜的那款就行了。</div>

### Python  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Python3.8或以上版本  

### 游戏设置
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;启动脚本前，一定要确认好客户端设置的游戏缩放模式是【经典模式】还是【极致模式】，如果游戏客户端缩放模式与启动的脚本不一致，会导致无法识别到图像的。  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Q: 如何确认自己游戏缩放设置?  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;A: 游戏启动界面--左下角【游戏设置】-- 第一行【游戏缩放模式设置】，默认为【经典模式】  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;注意: releases 只打包了“经典模式”，如果需要"极致模式"请自行打包，打包文件为“main_ultimate.spec”，打包库为Pyinstaller  

### 游戏窗口分辨率  

* 为了保证精度请确保分辨率大于 “1366*768” 。小于此分辨率切图会缩放变形，切图模板会无法识别。    
窗口或者全屏模式不影响脚本的运行。  

* 请保证游戏画面完整的显示在屏幕上，不要将窗口的部分画面移动到窗口之外，会影响画面识别。

##  功能说明事项  
----
<div align=center>
<img src="https://github.com/moonlessdark/JiuYinDance/blob/master/Resources/Readme/主界面.PNG">
</div>   

### 已经实现的功能  
 - 团练授业  
 - 上下左右(绿色/红色背景的)  
 - 武庆礼卡(9点开卡)，只会开2次卡。侠骨区第三次开卡没钱。
 - 押镖(需要设置打怪技能)
 - 地图物资采集(挖矿、砍树)
 - 玄机秘境自动报名(8点整报名),单纯的报名，没有其他功能。
 - 游戏自动截图  
 - 漠西风涛-挖宝指引,使用方法参考[此帖子](https://tieba.baidu.com/p/9124698712) ，此功能的入口在**菜单栏-小工具**中，不需要“幽灵键鼠”也可以使用。  


### 关于团练授业，隐士势力的修炼  
* 注意：功能列表中的“隐士势力”不是指隐士势力中的日常任务，而是某些隐士势力会有绿色的 “上下左右JK” 按钮。
* 当前版本在**望辉洲**的舞蹈周长，**天涯海阁**的瀑布修炼、钓鱼，**古墓**的密室修炼， 挖宝活动中BOSS的修罗刀为绿色按钮。BOSS*鬼阎王*为红色背景的按钮。    

* 游戏过程中，如果切换了画质，请进出一下家园或者切换一下地图场景，让游戏渲染的画面重新加载一下，再重新打开脚本，避免识别异常。

* 授业时最多只支持2个号在同一个场景同时授业，因为不持支绑定窗口，所以只能按了一轮后再切换另一个窗口按按钮。  
3个号的时候时间来不及。建议要3开授业时，最好分开到2个场景。     

* 按钮执行时，请不要打开聊天框进行聊天，不然团练的按钮会直接输入到你的聊天框里面去了。  
同时，在按钮执行时，请不要干扰窗口，不要做其他操作，因为我只会在按钮执行前激活一次窗口，如果按钮在执行过程中窗口激活状态被干扰，会导致按钮失败。   

* 如果你的电脑双开时有窗口切换失败的问题，请 **[参考此教程](https://blog.csdn.net/qq_26013403/article/details/129122971)** 的方法修改注册表并重启电脑，以管理员权限运行脚本。如果依旧有问题的话我暂时也没撤了，只能进行单开团练授业。  

### 关于押镖任务  

*  押镖地图推荐: 洛阳和燕京。  
*  暂时只支持单人运镖。  
*  <b><font color=red>镖车打怪时，请不要用鼠标点击窗口，不然会导致“格挡”NPC技能的按键无效。</font></b>
*  <font color=red>在使用押镖之前，请先去菜单栏“配置”-“编辑技能”文件修改一下您的技能按键。</font>  
 
<div align=center>
<img src="https://github.com/moonlessdark/JiuYinDance/blob/master/Resources/Readme/%E6%8A%80%E8%83%BD%E8%AE%BE%E7%BD%AE.PNG">
</div>

* 注意: 怒气招请的优先级请设置为最低。因为没有判断当前角色的“怒气值”是否足够。或者怒气招如果是加BUFF类型的，干脆就不填写此招式。  
* 如果您也是一个峨眉使用金鼎套路，那么就只需要修改对应的 “Key”(技能对应的键盘按键)即可。 
* 押镖时建议先按F8屏幕一下其他玩家，减少干扰。  
* 目前还没有做过多的干扰项判断(比如垃圾四害的干扰)，在打劫镖的NPC时，会受到游戏内的横幅提示的影响。(例如：某某帮会发动了追杀，某某玩家砸蛋出了金丝粉)，横幅会的出现会遮挡劫镖NPC放技能的图标，导致人物无法格挡技能被击飞，影响后续的镖车判断。  

### 关于物资采集
<div align=center>
<img src="https://github.com/moonlessdark/JiuYinDance/blob/master/Resources/Readme/%E7%89%A9%E8%B5%84%E9%87%87%E9%9B%86.PNG">
</div>

*  请先设置好采集的路径,将地图中物资(矿石、树木)的坐标填写到表格中。
*  经过实测，自动砍树的效果很不好(暂时还没有更好的方案)，因为自动寻路时经常会卡地形，无法正常自动寻路到 树木的旁边，所以具体的砍树路径请自行探索。
*  脚本执行的过程中，每隔10秒会用鼠标点击小地图检测一遍当前坐标，判断人物角色是否还在移动中，所以请不要和脚本抢鼠标。  
*  采集之前请先确保包裹中有采集道具。  
*  首次运行新路线时,需要人工监控。  
*  如果出现坐标在点击小地图时没用采集而是向其他方法移动,说明此坐标地形干扰大。请尝试调整坐标(x或者y轴加减1反复调试)。
*  如果物资旁边有个NPC,在自动采集时很大概率会自动点击到此NPC,这种坐标请跳过。

### 关于漠西-挖宝指引  
<div align=center>
<img src="https://github.com/moonlessdark/JiuYinDance/blob/master/Resources/Readme/%E6%BC%A0%E8%A5%BF%E6%8C%96%E5%AE%9D.png">
</div>  

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;说明: 由于原来的地图是一张3500X3500分辨率的图片，为了映射到小地图(900X900)，势必会产生精度丢失。所以2条虚线相交并不一定代表挖宝的位置一定准确。  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;到了那附近后还需要根据指引方向寻找一下宝箱。一般差的不远，都是在那附近的。    
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;本功能是图色识别，所以在传送到新的复活点后，必须等右上角的指针加载出来后，才能点击“绘制连线”。

* 第一步: 传送至某个复活点  
* 第二步: 在窗口右上角，点击“绘制坐标连线”  
* 第三步: 点击移动至XXX, 具体移动到哪里根据你当前人物所在的复活点  
* 第四步: 再传送到一个新的复活点，具体是哪里根据绘制的第一条虚线来判断，最好是相对的。  
* 第五步: 继续绘制一条新的连线，并点击 移动到XXX  
* 第六步: 让人物角色移动到2条虚线相交的地方。  


## 关于安全性  
----
* 任何脚本都有被发现的风险。  
* 此脚本未绑定窗口，尽量减少被发现的几率。  
* 键盘操作调用幽灵键鼠，截图操作调用windowsapi，图片识别使用opencv处理。  
* 按钮之间增加随机等待时间，尽量表现的像个人(但是会影响执行速度，表现出的效果就是按键的时候时快时慢)  
<br>
<br>
