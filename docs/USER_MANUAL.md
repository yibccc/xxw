# 定时器服务 - 用户手册

## 概述

定时器服务是一款基于 Web 的定时任务管理工具，支持创建一次性定时器和每日重复定时器。当定时器触发时，系统会实时推送通知给您。

**默认账号：**
- 管理员：`admin` / `admin`
- 普通用户：`user` / `123456`

在线体验地址： http://april4us.top:5000/login

---

## 目录

1. [登录与注册](#1-登录与注册)
2. [定时器管理](#2-定时器管理)
3. [事件中心](#3-事件中心)
4. [常见问题](#4-常见问题)

---

## 1. 登录与注册

### 1.1 登录

![image-20260313135058416](https://yibccc.oss-cn-hangzhou.aliyuncs.com/typora/image-20260313135058416.png)

访问系统后，输入用户名和密码登录。

```
用户名：admin
密码：admin

or

用户名：test
密码：123456
```

![image-20260313135123053](https://yibccc.oss-cn-hangzhou.aliyuncs.com/typora/image-20260313135123053.png)

### 1.2 注册新用户

![image-20260313135142478](https://yibccc.oss-cn-hangzhou.aliyuncs.com/typora/image-20260313135142478.png)

点击注册链接，创建新账号。

**注册要求：**
- 用户名：3-50 个字符
- 密码：至少 6 个字符

---

## 2. 定时器管理

### 2.1 创建定时器

![image-20260313135215322](https://yibccc.oss-cn-hangzhou.aliyuncs.com/typora/image-20260313135215322.png)

在定时器列表页面，点击「新建定时器」按钮。

#### 2.1.1 创建一次性定时器（Once）

适用于单次提醒场景，例如「5分钟后提醒我开会」。

```
名称：提醒开会
类型：一次性
延迟时间：5 分钟
```

![image-20260313135242200](https://yibccc.oss-cn-hangzhou.aliyuncs.com/typora/image-20260313135242200.png)

#### 2.1.2 创建每日定时器（Daily）

适用于重复提醒场景，例如「每天早上8点提醒晨会」。

```
名称：晨会提醒
类型：每日
触发时间：08:00
```

![image-20260313135321597](https://yibccc.oss-cn-hangzhou.aliyuncs.com/typora/image-20260313135321597.png)

### 2.2 编辑定时器

![image-20260313135346779](https://yibccc.oss-cn-hangzhou.aliyuncs.com/typora/image-20260313135346779.png)

点击定时器右侧的编辑按钮，修改延迟时间或触发时间。

### 2.3 删除定时器

![image-20260313135404874](https://yibccc.oss-cn-hangzhou.aliyuncs.com/typora/image-20260313135404874.png)

点击删除按钮，确认后定时器将被软删除。

---

## 3. 事件中心

### 3.1 查看事件

![image-20260313135837044](https://yibccc.oss-cn-hangzhou.aliyuncs.com/typora/image-20260313135837044.png)

![image-20260313135829443](https://yibccc.oss-cn-hangzhou.aliyuncs.com/typora/image-20260313135829443.png)

当定时器触发时，会生成事件记录。您可以在事件中心查看所有触发事件。

**事件状态：**
- 未读（高亮显示）
- 已读

### 3.2 标记已读

![image-20260313135534778](https://yibccc.oss-cn-hangzhou.aliyuncs.com/typora/image-20260313135534778.png)

- 点击单条事件的「确认」按钮标记为已读
- 点击「全部确认」批量标记所有未读事件为已读

### 3.3 实时推送

![image-20260313135513702](https://yibccc.oss-cn-hangzhou.aliyuncs.com/typora/image-20260313135513702.png)

当定时器触发时，系统会通过 SSE 实时推送通知，无需刷新页面。

---

## 4. 常见问题

### Q1: 定时器创建后多久触发？

- **一次性定时器**：按照设置的延迟时间精确触发
- **每日定时器**：每天在设置的时间点触发

### Q2: 可以暂停定时器吗？

不可以。定时器创建后自动启用，不支持暂停功能。如需停止，可以删除定时器。

### Q3: 一次性定时器触发后会怎样？

一次性定时器触发后状态会自动变为「已完成」，不会再次触发。

---

*文档版本：1.0*
*更新日期：2026-03-12*