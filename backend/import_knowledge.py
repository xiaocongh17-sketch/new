"""批量导入知识库文档到 AI Store Copilot。

用法:
  # 导入示例数据（推荐先跑这个）
  python import_knowledge.py --sample

  # 导入单个文件
  python import_knowledge.py --file ./销售话术.txt --category SOP --title "销售标准话术"

  # 批量导入整个目录
  python import_knowledge.py --dir ./knowledge_files --category FAQ

支持的分类: SOP（流程规范）, TRAINING（培训资料）, FAQ（常见问题）, MARKET（市场数据）
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error


API_BASE = "http://localhost:8000/api/v1"

# ===== 知识库示例数据 =====
SAMPLE_DATA = [
    {
        "title": "房源信息收集标准流程",
        "category": "SOP",
        "content": """【房源收集流程】
1. 业主委托：接到业主出租咨询后，记录房屋基本信息（地址、面积、户型、楼层、装修）
2. 现场勘查：24小时内安排实地拍照，确认房屋实际状况
3. 价格评估：参考同小区同户型近期成交价，给出合理建议租金
4. 签订委托：与业主签订《房屋出租委托协议》，明确委托期限和佣金比例
5. 房源上架：在系统中创建房源，上传照片，设置租金和标签""",
    },
    {
        "title": "客户带看标准流程",
        "category": "SOP",
        "content": """【客户带看流程】
1. 预约确认：提前30分钟与客户确认看房时间和地点
2. 准备资料：准备房屋钥匙、看房确认单、户型图、测距仪
3. 带看前：提前15分钟到达，检查房屋卫生和设施
4. 带看中：介绍房屋亮点（装修、采光、配套），了解客户需求
5. 带看后：填写客户反馈，24小时内跟进客户意向
6. 系统记录：在CRM中更新带看记录和客户意向等级""",
    },
    {
        "title": "签约成交标准流程",
        "category": "SOP",
        "content": """【签约成交流程】
1. 资质审核：核实租客身份证/护照，业主房产证
2. 合同准备：使用标准《房屋租赁合同》，填写双方信息、租金、押金、租期
3. 合同签署：双方现场签署合同，一式三份（租客、业主、中介各一份）
4. 费用收取：收取租金（押一付三或协商）、中介服务费（一个月租金）
5. 物业交接：抄水电煤气表、交接钥匙门禁卡、登记物业联系方式
6. 售后跟进：入住后7天回访，了解入住情况""",
    },
    {
        "title": "中介费怎么收？",
        "category": "FAQ",
        "content": """【中介服务费标准】
- 住宅租赁：成交后收取一个月租金作为中介服务费
- 商业租赁：成交后收取半个月至一个月租金
- 费用由谁承担：通常租客和业主各承担一半，也可协商由一方承担
- 特殊情况：老客户续租可享受8折优惠""",
    },
    {
        "title": "出租需要房东提供什么材料？",
        "category": "FAQ",
        "content": """【业主出租所需材料】
1. 身份证原件及复印件
2. 房产证原件及复印件
3. 房屋钥匙（至少两套）
4. 水电煤气卡/账号
5. 物业缴费凭证（如需证明无欠费）
6. 授权委托书（如果业主不在本地，需公证委托）""",
    },
    {
        "title": "租客需要提供什么材料？",
        "category": "FAQ",
        "content": """【租客租房所需材料】
1. 身份证原件及复印件
2. 工作证明或在读证明
3. 收入证明（可选，部分业主要求）
4. 押金和首期租金
5. 紧急联系人信息""",
    },
    {
        "title": "房屋交接注意事项",
        "category": "FAQ",
        "content": """【房屋交接清单】
- 水电煤气：拍照记录当前读数，结清前任费用
- 钥匙门禁：清点钥匙数量，测试门禁卡
- 家电家具：检查空调、热水器、燃气灶等能否正常使用
- 网络宽带：确认是否有网络，如需新装需业主同意
- 物业登记：到物业处办理租客入住登记
- 车位情况：如有车位需单独确认""",
    },
    {
        "title": "电话邀约话术技巧",
        "category": "TRAINING",
        "content": """【电话邀约三步走】
第一步：自我介绍与破冰（15秒）
"您好，我是XX房产的小张，请问您现在方便说话吗？"

第二步：价值陈述（30秒）
"我这边有一套非常适合您的房子，在XX小区，XX平米，XX价格，您有兴趣了解一下吗？"

第三步：邀约看房（15秒）
"要不我们约个时间实地看看？您今天下午方便还是明天上午方便？"

注意事项：
- 语速适中，语气热情但不急促
- 先问方不方便，不要直接开始长篇介绍
- 二选一邀约，提高成功率""",
    },
    {
        "title": "如何处理客户异议",
        "category": "TRAINING",
        "content": """【常见异议处理话术】

异议1：价格太贵
"我理解您觉得价格偏高，这个价格其实包含了小区最好的采光和视野，而且同户型最近都涨了。"

异议2：我再考虑考虑
"好的，不过这套房子看的人挺多的，昨天就有三组客户来看过。要不我先帮您保留一下？"

异议3：我要和家里人商量
"应该的，买房是大事。您看有哪些问题需要和家人确认的，我先帮您把资料整理好。"

核心原则：先认同 → 再解释 → 最后给方案""",
    },
    {
        "title": "2024-2025年租金市场行情",
        "category": "MARKET",
        "content": """【市场行情参考】
- 一居室（40-60㎡）：月租金 3500-5500 元
- 两居室（60-90㎡）：月租金 4500-7500 元
- 三居室（90-130㎡）：月租金 6000-10000 元
- 装修溢价：精装比简装高 20-30%
- 楼层溢价：中高层（5-20层）比低层高 10-15%
- 地铁房溢价：距地铁500米内溢价 15-25%

数据来源：2024-2025年区域成交数据统计""",
    },
]


def _request(method, path, data=None, token=None):
    """Make HTTP request using built-in urllib."""
    url = f"{API_BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")[:120]
        raise RuntimeError(f"HTTP {e.code}: {err_msg}")


def login():
    """Login and get access token."""
    result = _request("POST", "/auth/login", {"wecom_userid": "ww7ee68b692eb16095"})
    return result["access_token"]


def import_document(token, doc):
    """Import a single document."""
    try:
        _request("POST", "/knowledge", doc, token)
        print(f"  [OK] {doc['title']} (分类: {doc['category']})")
        return True
    except Exception as e:
        print(f"  [FAIL] {doc['title']}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="批量导入知识库文档")
    parser.add_argument("--file", type=str, help="导入单个文件")
    parser.add_argument("--dir", type=str, help="导入整个目录")
    parser.add_argument("--category", type=str, default="FAQ",
                        choices=["SOP", "TRAINING", "FAQ", "MARKET"],
                        help="文档分类")
    parser.add_argument("--title", type=str, help="文档标题（单个文件时使用）")
    parser.add_argument("--sample", action="store_true",
                        help="导入示例数据（房地产经纪人知识库）")
    parser.add_argument("--server", type=str, default="http://localhost:8000",
                        help="后端服务器地址")
    args = parser.parse_args()

    global API_BASE
    API_BASE = f"{args.server}/api/v1"

    docs_to_import = []

    if args.sample:
        print("[准备导入 10 篇示例知识库文档...]")
        docs_to_import = SAMPLE_DATA

    elif args.file:
        if not os.path.exists(args.file):
            print(f"[错误] 文件不存在: {args.file}")
            return
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
        title = args.title or os.path.splitext(os.path.basename(args.file))[0]
        docs_to_import = [{"title": title, "category": args.category, "content": content}]

    elif args.dir:
        if not os.path.exists(args.dir):
            print(f"[错误] 目录不存在: {args.dir}")
            return
        files = sorted(f for f in os.listdir(args.dir) if f.endswith((".txt", ".md")))
        if not files:
            print(f"[错误] 目录中没有 .txt/.md 文件: {args.dir}")
            return
        for filename in files:
            filepath = os.path.join(args.dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            if content.startswith("# "):
                title = content.split("\n")[0].lstrip("# ").strip()
            else:
                title = os.path.splitext(filename)[0]
            docs_to_import.append({"title": title, "category": args.category, "content": content})

    else:
        parser.print_help()
        print("\n提示: 运行 python import_knowledge.py --sample 导入示例数据")
        return

    try:
        print(f"\n[正在导入 {len(docs_to_import)} 篇文档...]\n")
        token = login()
        print("[登录成功]\n")

        success = 0
        for doc in docs_to_import:
            if import_document(token, doc):
                success += 1

        print(f"\n[完成] 导入成功: {success}/{len(docs_to_import)} 篇")
    except Exception as e:
        print(f"\n[失败] 导入出错: {e}")
        print("   请确认后端服务已启动: http://localhost:8000")


if __name__ == "__main__":
    main()
