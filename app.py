# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
from aip import AipFace
import base64
import random

app = Flask(__name__)

# ▼▼▼ 你的百度云密钥 (保持不变) ▼▼▼
APP_ID = '7402717'
API_KEY = '1khVNppDfSauhpmEFMlp8EPe'
SECRET_KEY = '9fIs1JIFu9gHkZD8vWVujerZ7IdnsFYZ'

client = AipFace(APP_ID, API_KEY, SECRET_KEY)

# ▼▼▼ 1. 修改这里：设置你的私密邀请码 ▼▼▼
VALID_CODES = ["GEX7KD"] 

# --- 数据与文案库 (保持原样) ---
DETAIL_DB = {
    "senses": [
        {"key": "eye_brow", "name": "眉眼协调度", "high": ("眉眼间距适中，符合黄金比例", "眉形与眼睛弧度完美呼应"), "low": ("可通过眉形微调优化眉眼关系", "加强睫毛护理增强表现力")},
        {"key": "nose_3d", "name": "鼻部立体度", "high": ("鼻梁高度适中，比例协调", "鼻尖形状精致"), "low": ("可通过鼻影修饰增强立体感", "注意表情管理避免鼻翼扩张")},
        {"key": "lip_shape", "name": "唇形美观度", "high": ("唇厚度比例接近1:1.5标准", "唇峰明显，唇形清晰"), "low": ("可通过唇线修饰优化唇形", "注意唇部保湿避免干纹")},
        {"key": "ratio", "name": "三庭五眼", "high": ("三庭比例接近1:1:1标准", "面部纵横比符合美学标准"), "low": ("可通过发型调整优化比例", "注意避免习惯性表情影响对称")}
    ],
    "bone": [
        {"key": "cheek", "name": "颧骨立体度", "high": ("颧骨位于黄金分割点", "提供良好的面部支撑"), "low": ("可通过修容强化立体感", "保持适当面部脂肪层")},
        {"key": "jaw", "name": "下颌线清晰度", "high": ("下颌角接近120度标准", "线条清晰流畅"), "low": ("可通过颈部锻炼强化下颌线", "避免体重波动影响轮廓")},
        {"key": "forehead", "name": "额头饱满度", "high": ("额头高度符合标准", "发际线形状优美"), "low": ("可通过发型修饰额头比例", "关注发际线养护")},
        {"key": "profile", "name": "侧面轮廓", "high": ("符合四高三低美学标准", "侧面线条流畅"), "low": ("通过发型增强侧面表现力", "保持良好体态避免颈前倾")}
    ],
    "skin": [
        {"key": "smooth", "name": "皮肤光滑度", "high": ("表面光滑，无粗糙感", "纹理清晰有序"), "low": ("定期去角质提升光滑度", "注意防晒避免粗糙")},
        {"key": "color", "name": "肤色均匀度", "high": ("肤色均匀，无明显色差", "整体协调一致"), "low": ("加强局部暗沉护理", "使用均匀肤色产品")},
        {"key": "tight", "name": "皮肤紧致度", "high": ("弹性良好，恢复迅速", "胶原蛋白充足"), "low": ("加强抗衰护理预防松弛", "保持水分维持弹性")},
        {"key": "health", "name": "肤质健康度", "high": ("屏障完整，锁水良好", "无明显敏感反应"), "low": ("避免过度清洁", "根据季节调整护肤")}
    ]
}

TYPES_DB = {
    "sweet": {"title": "甜系美人", "badge": "甜美", "desc": "您的面部特征柔和，具有明显的甜美气质。眼睛大而圆，软组织饱满，给人一种亲切可爱的感觉，非常有观众缘。", "tags": ["初恋感", "元气满满", "甜系"]},
    "cool": {"title": "清冷美人", "badge": "清冷", "desc": "骨骼感较强，五官线条利落，自带一种高级的疏离感。这种长相非常耐看，往往是时尚界的宠儿。", "tags": ["骨相优越", "高级厌世", "清冷"]},
    "standard": {"title": "标准美人", "badge": "端庄", "desc": "三庭五眼比例非常标准，无论是骨相还是皮相都挑不出错。这种端庄大气的长相非常抗老，属于典型的东方审美。", "tags": ["比例完美", "端庄大气", "国泰民安"]}
}

MAKEUP_DB = {
    "base": {"title": "底妆重点", "content": "营造水光肌效果，使用光泽型粉底，展现皮肤饱满感"},
    "eye": {"title": "眼妆技巧", "content": "强调圆眼效果，使用粉色或棕色眼影，加强卧蚕和睫毛"},
    "blush": {"title": "腮红选择", "content": "选择粉嫩色系，以圆形打法扫在苹果肌，增强可爱感"},
    "lip": {"title": "唇妆搭配", "content": "选择水润质地，颜色以粉色、珊瑚色等甜美色系为主"},
    "brow": {"title": "眉形设计", "content": "眉毛形状柔和，避免过于锋利的眉峰，营造毛茸茸感"},
    "high": {"title": "高光运用", "content": "在苹果肌、唇峰、下巴添加细微珠光，增强甜美光泽感"}
}

def generate_sub_item(base_score, config):
    score = round(base_score + random.uniform(-0.5, 0.8), 1)
    if score > 9.9: score = 9.9
    if score < 6.0: score = 6.0
    return {
        "name": config["name"], "score": score, "width": score * 10,
        "pro": config["high"][0] if score > 8 else config["high"][1],
        "con": config["low"][0] if score > 8 else config["low"][1]
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify_code', methods=['POST'])
def verify_code():
    code = request.json.get('code')
    if code in VALID_CODES: return jsonify({"success": True})
    return jsonify({"success": False, "msg": "邀请码错误，请联系管理员获取"})

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files: return jsonify({"error": "请上传照片"}), 400
    file = request.files['file']
    img_content = file.read()
    image = base64.b64encode(img_content).decode('utf-8')
    try:
        result = client.detect(image, "BASE64", {"face_field": "age,beauty,face_shape,gender,skin"})
        if result['error_code'] == 0:
            face = result['result']['face_list'][0]
            raw_score = face['beauty']
            total_score = round((raw_score / 100 * 3.0) + 6.8, 1)
            if total_score > 9.8: total_score = 9.8
            
            senses_data = [generate_sub_item(total_score, item) for item in DETAIL_DB["senses"]]
            bone_data = [generate_sub_item(total_score, item) for item in DETAIL_DB["bone"]]
            skin_data = [generate_sub_item(total_score, item) for item in DETAIL_DB["skin"]]
            
            t_key = "sweet" if face['face_shape']['type'] == 'round' else "standard"
            if total_score > 9.0: t_key = "cool"
            
            return jsonify({
                "success": True, "total_score": total_score,
                "details": {"senses": senses_data, "bone": bone_data, "skin": skin_data},
                "type_info": TYPES_DB[t_key], "makeup": MAKEUP_DB
            })
        else:
            return jsonify({"success": False, "msg": "未检测到人脸"})
    except Exception as e:
        print(e)
        return jsonify({"success": False, "msg": "系统繁忙"})

if __name__ == '__main__':

    app.run(debug=True, port=5000)
