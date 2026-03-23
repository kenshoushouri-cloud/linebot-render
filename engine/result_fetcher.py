import requests
from bs4 import BeautifulSoup

def fetch_race_result(place, race_number, date):
    """
    公式サイトから結果を取得（簡易版）
    """
    url = f"https://www.boatrace.jp/owpc/pc/race/raceresult?jcd={place}&rno={race_number}&hd={date}"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    # 着順
    ranks = soup.select(".is-fs18")
    if len(ranks) < 3:
        return None, None

    result = [int(r.text.strip()) for r in ranks[:3]]

    # オッズ
    odds = soup.select(".oddsPoint")
    odds_dict = {"trifecta": float(odds[0].text.replace(",", ""))} if odds else {}

    return result, odds_dict
