Question List
-------------
url: http://fenbi.com/android/xingce/exercises
method: POST
params: dict
    - keypointId: 题目重点（可忽略）
    - type: 格式 => 2: 考卷, 3: 专项练习, 4: 错题
    - limit: 题数限制
cookies: {
    sess: value,
    persistent: value,
    userid: value,
    sid: value
}
return: JSON
    - id: 此练习ID
    - userId: 用户ID
    - createdTime: 创建时间
    - updatedTime: 更新时间
    - status: 状态
    - quizId: 练习集ID
    - client: 客户端
    - version: 版本
    - userAnswers: 未知
    - elapsedTime: 消耗时间
    - currentTime: 当前时间
    - sheet: JSON
        - id: 表单ID
        - keypointId: 考点ID
        - type: 类型
        - name: 名称
        - paperId: 未知
        - questionCount: 习题数量
        - time: 限时
        - chapters: 章节 JSON list
        - questionIds: 题目列表 list
        - difficulty: 难度系数

Question Detail
---------------
url: http://fenbi.com/android/xingce/questions
params: ids -> sequence split by ,
method: GET
cookies: 同上
return: JSON list
    - id: 题目ID
    - content: 内容
    - material: 材料
    - type: 类型 1: 单选题, 
    - difficulty: 难度系数
    - createTime: 创建时间 -> timestamp
    - shortSource: 未知
    - accessories: 选项 dict list
        - options: 选项内容 -> list
        - type: 类型
    - correctAnswer: dict
        - choice: 正确选项
        - type: 类型

Solution
--------
url: http://fenbi.com/android/xingce/pure/solutions
method: GET
params: ids -> sequence split by ,
cookies: 同上
return: JSON list
    - id: 题目ID
    - solution: 解释
    - source: 出处
    - tags: 标签
    - flags: 未知
    - solutionAccessories: 未知

Question Meta
-------------
url: http://fenbi.com/android/xingce/question/meta
method: GET
params: ids -> sequence split by ,
cookies: 同上
return: JSON list
    - id: 题目ID
    - answerCount: 是否回答
    - wrongCount: 是否错误
    - totalCount: 总回答数
    - mostWrongAnswer: dict
        - choice: 选项
        - type: 类型
    - correctRatio: 准确率

Question Keypoint
-----------------
url: http://fenbi.com/android/xingce/solution/keypoints
method: GET
params: ids -> sequence split by ,
cookies: 同上
return: JSON list
    - id: 题目ID
    - name: 考点名称 (二级分类-三级分类)

Image
-----
url: http://fb.fbstatic.cn/api/xingce/images/{id}.png

Latex
-----
url: http://fb.fbstatic.cn/api/xingce/accessories/formulas?latex={sha1}&fontSize=48&color=666666

Category
--------
url: http://fenbi.com/android/xingce/categories
method: GET
cookies: 同上
return: JSON list
    - id: 一级类目ID
    - name: 一级类目名称
    - count: 一级类目数量
    - optional: 未知
    - children: 子类目 dict list
        - id: 二级类目ID
        - name: 二级类目名称
        - count: 二级类目数量
        - optional: 未知
        - children: 子类目 dict list
            - id: 三级类目ID
            - name: 三级类目名称
            - count: 三级类目数量
            - choiceOnly: 只有选择题
