from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from concurrent.futures import ThreadPoolExecutor
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import json
from datetime import datetime

# --- [설정] ---
MAX_WORKERS = 4  # 동시에 띄울 크롬 창 개수 (컴퓨터 성능에 따라 3~5 권장)
SN = "572"
MI = "27285"
URL = f"https://pangyo-h.goesn.kr/pangyo-h/presnatn/selectPresnatnSrchPage.do?mi={MI}&presnatnSn={SN}"

raw_data = "10101고연서10102김세빈10103김소율10104김수빈10105김원10106김재연10107김지원10108김진영10109김현준10110나연후10111박루나10112박주하10113신예주10114신재이10115유승원10116이선우10117이시원10118이하린10119장규언10120정민권10121정채원10122차준우10123최지훈10124최희진10125한담희10126홍성준10201권강우10202김도영10203김민관10204김민서10205김아린10206김재윤10207김준범10208김하영10209김효빈10210배효빈10211서연우10212심채은10213엄시우10214윤휘성10215이유진10216이정진10217이혜민10218임태윤10219전빛나10220정애린10221진가인10222최고은10223최윤호10224최은수10225한상혁10226 한유진10301권민석10302김경률10303김고은10304김연희10305김예린10306김재현10307문다몬10308민건우10309박서윤10310박정민10311박하민10312서하람10313석세영10314신준하10315양시호10316오승윤10317윤민상10318이건희10319이연교10320장예나10321장주하10322정유진10323정한나10324조은결10325천소은10326강건우10327안건우10401강무연10402강윤서10403국재영10404김도윤10405김민재10406김시후10407김예빈10408김정윤10409김태리10410박채은10411서준우10412안서진10413안수아10414양지훈10415이노아10416이동명10417이수민10418이예진10419이예함10420이정준10421이현준10422인지후10423전예찬10424차정우10425최유선10426황현준10501강지원10502김도영10503김도은10504김민찬10505김열매10506김효린10507문승원10508박선민10509안수인10510안주성10511양주혁10512유건우10513유준현10514이규원10515이다경10516이송하10517이시현10518이효훈10519인지성10520장재영10521정진우10522정채이10523지은찬10524최승훈10525최유진10526한정원10601강지호10602김동혁10603김수형10604김유건10605김윤후10606김재윤10607박서이10608박승원10609박윤민10610백지희10611백채민10612송가은10613신재이10614신지우10615유준상10616윤서영10617이우민10618이준석10619이지우10620인하영10621장유리10622정진10623차동빈10624피호은10625황하은10701강민진10702강윤재10703권지우10704김가은10705김나현10706김도은10707김준영10708김태윤10709노서현10710마준환10711문정원10712박보윤10713박주원10714유서영10715윤성민10716이상연10717이준영10718이지유10719이혜민10720이효진10721임연지10722정수범10723정시환10724정영훈10725최성진10726장현준10801권민성10802김현욱10803남지훈10804박규민10805박시은10806박지민10807백종훈10808서현진10809송영운10810송하람10811심예원10812이명준10813이상민10814이송연10815이은찬10816이하람10817장준기10818전수빈10819정서현10820조은서10821최동식10822최효제10823하동근10824홍예린10825황예림"
students = re.findall(r'(\d{5})\s*([^\d\s]+)', raw_data)

def process_student(student_info):
    old_id, name = student_info

    # 각 스레드별로 드라이버 생성
    options = Options()
    options.add_argument("--headless")  # 창을 숨기면 훨씬 빨라집니다 (보고 싶으면 주석 처리)
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(URL)
        # JS로 즉시 입력 (타이핑 시간 절약)
        driver.execute_script(f"document.getElementById('inqireCndSrch01').value='{name}';")
        driver.execute_script(f"document.getElementById('inqireCndSrch02').value='{old_id}';")
        # 검색 함수 직접 호출 (클릭보다 빠름)
        driver.execute_script("presnatnResultSrch();")

        time.sleep(1.0)  # 결과 로딩 대기

        # 결과 긁기
        row = driver.find_element(By.CSS_SELECTOR, "tbody tr")
        tds = row.find_elements(By.TAG_NAME, "td")
        if len(tds) >= 5:
            new_id = f"2{tds[3].text.strip().zfill(2)}{tds[4].text.strip().zfill(2)}"
            print(f"{old_id} {name}: {new_id}")
            return {
                "oldId": old_id,
                "name": name,
                "newId": new_id,
                "status": "success"
            }
    except Exception:
        pass
    finally:
        driver.quit()

    return {
        "oldId": old_id,
        "name": name,
        "newId": None,
        "status": "failed"
    }

# 실행
if __name__ == "__main__":
    print(f"--- {MAX_WORKERS}개 창으로 분산 조회 시작 ---")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(process_student, students))

    payload = {
        "meta": {
            "source": "craw.py",
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "total": len(results),
            "success": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "failed")
        },
        "students": results
    }

    with open("pangyo_fast_results.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("--- 모든 조회 완료 ---")
