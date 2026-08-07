from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

# ------------------------------------------------------------------
# Riot의 "Data Dragon"이라는 정적 데이터 서버에서 챔피언 데이터를 가져온다.
# 이건 API 키가 필요 없는 공개 데이터라서 그냥 바로 쓸 수 있어.
# ------------------------------------------------------------------

def get_latest_version():
    versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    versions = requests.get(versions_url).json()
    return versions[0]


# 버전 번호는 앱이 켜질 때 딱 한 번만 물어보고 계속 재사용한다.
LATEST_VERSION = get_latest_version()


def get_champions():
    # 전체 챔피언 목록(요약 정보)을 가져온다.
    champ_url = f"https://ddragon.leagueoflegends.com/cdn/{LATEST_VERSION}/data/ko_KR/champion.json"
    data = requests.get(champ_url).json()

    champions = []
    seen_names = set()  # 이미 추가한 챔피언 이름을 기억해두는 용도

    for champ_key, champ_info in data["data"].items():
        name = champ_info["name"]

        # 이미 같은 이름의 챔피언을 추가했다면 건너뛴다 (중복 방지)
        if name in seen_names:
            continue
        seen_names.add(name)

        champions.append({
            "id": champ_key,                      # 예: "Ahri"  (URL, 이미지 파일명에 씀)
            "name": name,                          # 예: "아리"
            "title": champ_info["title"],          # 예: "구미호"
            "tags": champ_info["tags"],            # 예: ["Mage", "Assassin"]  <- 역할군
            "image": (
                f"https://ddragon.leagueoflegends.com/cdn/"
                f"{LATEST_VERSION}/img/champion/{champ_info['image']['full']}"
            ),
        })

    # 이름 가나다순으로 정렬
    champions.sort(key=lambda c: c["name"])
    return champions


def get_champion_detail(champ_id):
    """
    챔피언 한 명의 자세한 정보(패시브 + Q/W/E/R 스킬)를 가져온다.
    champ_id는 "Ahri" 처럼 영어로 된 챔피언 고유 ID다.
    """
    detail_url = (
        f"https://ddragon.leagueoflegends.com/cdn/"
        f"{LATEST_VERSION}/data/ko_KR/champion/{champ_id}.json"
    )
    data = requests.get(detail_url).json()
    champ_info = data["data"][champ_id]

    # 얼굴 아이콘(작은 원형 이미지)
    icon_url = (
        f"https://ddragon.leagueoflegends.com/cdn/"
        f"{LATEST_VERSION}/img/champion/{champ_info['image']['full']}"
    )

    # 스플래시 아트(상세 페이지 상단 배경 이미지)
    splash_url = (
        f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champ_id}_0.jpg"
    )

    # 패시브 스킬
    passive = {
        "name": champ_info["passive"]["name"],
        "description": champ_info["passive"]["description"],
        "image": (
            f"https://ddragon.leagueoflegends.com/cdn/"
            f"{LATEST_VERSION}/img/passive/{champ_info['passive']['image']['full']}"
        ),
    }

    # Q, W, E, R 스킬 (spells 리스트 순서가 곧 Q → W → E → R 순서다)
    skill_keys = ["Q", "W", "E", "R"]
    spells = []
    for key, spell in zip(skill_keys, champ_info["spells"]):
        spells.append({
            "key": key,
            "name": spell["name"],
            "description": spell["description"],
            "image": (
                f"https://ddragon.leagueoflegends.com/cdn/"
                f"{LATEST_VERSION}/img/spell/{spell['image']['full']}"
            ),
        })

    return {
        "id": champ_id,
        "name": champ_info["name"],
        "title": champ_info["title"],
        "tags": champ_info["tags"],
        "icon": icon_url,
        "splash": splash_url,
        "passive": passive,
        "spells": spells,
    }


# 서버 켤 때 딱 한 번만 목록을 가져와서 저장해둔다.
CHAMPIONS = get_champions()


@app.route("/")
def home():
    return render_template("index.html", champions=CHAMPIONS)


@app.route("/champion/<champ_id>")
def champion_detail(champ_id):
    # URL 예시: /champion/Ahri  →  아리 상세 페이지
    champ = get_champion_detail(champ_id)
    return render_template("champion.html", champ=champ)


if __name__ == "__main__":
    app.run(debug=True)
