# Patent爬取结果说明

由于网站有访问速度限制，不使用IP池的话多进程跑很容易就被锁IP，所以单进程跑的。网站很慢，今天早上还误关了一次，跑了整整一天。以下是字段说明

- patent：你给的patent.txt中的值
- patent_id：瞎写的，我不知道是什么，详细是啥请看截图
- inv：瞎写的，我不知道是什么，详细是啥请看截图
- inv_date：瞎写的，我不知道是什么，详细是啥请看截图
- abstract：**Abstract**
- inventors：**Inventors**
- assignee：**Assignee**
- family_id：**Family ID**
- appl_no：**Appl. No.**
- filed：**Filed**
- related_patents：页面上的**Related U.S. Patent Documents**，不同行之间用" || "做分隔符，同一行之间用" | "做分隔符，整体在excel中是一个单元格，里边是长文本
- current_us_class：**Current U.S. Class**
- current_cpc_class：**Current CPC Class**
- current_international_class：**Current International Class**
- field_of_search：**Field of Search**
- us_cited_patents：**References Cited**下的**U.S. Patent Documents**，不同行之间用" || "做分隔符，同一行之间用" | "做分隔符，整体在excel中是一个单元格，里边是长文本
- foreign_cited_patents：**References Cited** 下的**Foreign Patent Documents**，不同行之间用" || "做分隔符，同一行之间用" | "做分隔符，整体在excel中是一个单元格，里边是长文本
- description：**Description** 段落间使用" || "做分隔符
- mohudu：计算过慢，还没算，我先把数据都抓下来
- keduxing：计算过慢，还没算，我先把数据都抓下来
- mohudu_fog：计算过慢，还没算，我先把数据都抓下来