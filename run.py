# 인터파크 여행지 검색 -> 결과
# 로그인 시 PC 버전 어려울 경우 -> 모바일 로그인으로 처리
# 모듈 가져오기
# pip3 install selenium
# pip3 install bs4
# pip3 install pymysql

from selenium import webdriver as wd
from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By
# 명시적 대기를 위해서 import
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from DbMgr import DBHelper as Db
import time
from Tour import TourInfo

# 사전에 필요한 정보 로드 => 디비, 쉘, 배치 파일에서 인자로 받아서 세팅. /가 중요한다고 한다.
db = Db()
main_url = 'http://tour.interpark.com/'
keyword = '로마'
# 상품 정보를 담는 리스트 (TourInfo 리스트))
tour_list = []

# 드라이버 로드
driver = wd.Chrome(executable_path = '/usr/local/Caskroom/chromedriver/2.40/chromedriver')

# 차후에 옵션 부여하여 (프록시, 에이전트 조작, 이미지 배제 등) 조작 가능

# 크롤링 오래 돌리면 임시파일들이 쌓인다! => Temp 파일들 삭제 요망. (맥도 그런가?)

# 사이트 접속 (get)
driver.get(main_url)

# 검색창을 찾아서 검색어를 입력
# - id 값, class 이름, 관계도 순으로 따져보면 됨
# - id = SearchGNBText
driver.find_element_by_id('SearchGNBText').send_keys(keyword)
# - 수정할 경우 => 뒤에 내용이 붙어버림 => .clear() 후에 .send_keys() 해야 의도대로 된다.

# 검색 버튼을 클릭
# - class = search-btn
driver.find_element_by_css_selector('button.search-btn').click()

# 잠시 대기 => 페이지가 로드되고 나서 즉각적으로 데이터를 획득하는 행위는 자제해야 함.
# 명시적 대기 => 특정 요소가 로케이트 (발견될 때까지) 대기
try:
    element = WebDriverWait(driver, 10).until(
        # 지정한 한 개 요소가 올라오면 웨이트 종료
        EC.presence_of_element_located((By.CLASS_NAME, 'oTravelBox'))
    )
except Exception as e:
    print('오류 발생', e)

# 암묵적 대기 => DOM이 다 로드될 때까지 대기하고 먼저 로드되면 바로 진행
# - 요소를 찾을 특정 시간동안 DOM 풀링을 지시. 예를 들어 10초 이내라도 발견되면 바로 진행.
driver.implicitly_wait(10)

# 절대적 대기 => time.sleep(10) -> 클라우드 페어 (작은 회사의 디도스 방어 솔루션)

# 더보기 눌러서 게시판 진입
# - find_element_... 하면 첫번째 것만 찾아냄.
# - >가 자식을 뜻함.
driver.find_element_by_css_selector('.oTravelBox>.boxList>.moreBtnWrap>.moreBtn').click()

# 로그인을 해서 접근하는 사이트의 경우, 세션이 끊겨 데이터를 못 가져올 경우 발생. 특정 단위로 로그아웃, 로그인을 시도해야 함.
# 특정 게시물이 크롤링 도중 사라질 경우 => 팝업 발생 (없는 게시물입니다) => 팝업 처리 필요
# 게시판 스캔시 => 임계점(어디에서 끝내야 되는지)을 모름.
# 게시판 스캔 => 메타 정보 획득 => loop 돌려서 일괄적 방문 접근 처리

# searchModule.SetCategoryList(1, '') 스크립트 실행
# 16은 임시값, 게시물 페이지 넘어갔을때 현상 확인차 추가적으로 숫자 넣음.
for page in range(1, 2): #16):
    try:
        # 자바스크립트 구동하기
        driver.execute_script("searchModule.SetCategoryList(%s, '')" % page)
        time.sleep(2)
        print("%s 페이지 이동" % page)
        ##########################
        # 여러 사이트에서 정보를 수집할 경우 공통 정보 정의 단계 필요. (테이블)
        # 상품명, 코멘트, 기간1, 기간2, 가격, 평점, 썸네일, 링크(상품상세정보)
        boxItems = driver.find_elements_by_css_selector('.oTravelBox>.boxList>li')
        # 상품 개별 접근
        for li in boxItems:
            # 이미지를 링크값을 사용할 것인가? - 없어지면 못 씀.
            # 직접 다운로드해서 본인 서버에 업로드(ftp) 할 것인가? - 저작권 문제 있음.
            #print('상품명', li.find_element_by_css_selector('h5.proTit').text)
            #print('코멘트', li.find_element_by_css_selector('p.proSub').text)
            #print('가격', li.find_element_by_css_selector('strong.proPrice').text)
            #print('썸네일', li.find_element_by_css_selector('img').get_attribute('src'))
            #print('링크', li.find_element_by_css_selector('a').get_attribute('onclick'))
            #기간1, 기간2, 평점 추출.
            #for info in li.find_elements_by_css_selector('.info-row .proInfo'):
                #print(info.text)

            # 데이터 모음
            # li.find_elements_by_css_selector('.info-row .proInfo')[1].text,
            # 데이터가 부족하거나 없을수도 있기 때문에 인덱스 접근은 위험함.
            obj = TourInfo(
                li.find_element_by_css_selector('h5.proTit').text,
                li.find_element_by_css_selector('strong.proPrice').text,
                li.find_elements_by_css_selector('.info-row .proInfo')[1].text,
                li.find_element_by_css_selector('a').get_attribute('onclick'),
                li.find_element_by_css_selector('img').get_attribute('src')
            )
            tour_list.append(obj)
            
    except Exception as e1:
        print('오류', e1)

print(tour_list, len(tour_list))

# 수집한 정보 개수를 루프 => 페이지 방문 => 콘텐츠 획득(상세정보) => DB 저장.
for tour in tour_list:
    #tour => TourInfo
    print(type(tour))
    # 링크 데이터에서 실데이터 획득
    # 분해
    arr = tour.link.split(',')
    if arr:
        # 대체
        link = arr[0].replace('searchModule.OnClickDetail(','')
        # 슬라이싱 - 첫 ' 와 마지막 ' 제거
        detail_url = link[1:-1]
        # 상세 페이지 이동 : URL 값이 완성된 형태인지 확인 필요 (http~)
        driver.get(detail_url)
        time.sleep(2)

        # 현재 페이지를 Beautiful Soup 의 DOM 으로 구성
        # driver.page_source 는 현재 화면의 html
        # driver.current_url 은 현재 화면의 url 
        soup = bs(driver.page_source, 'html.parser')
        # 현재 상세 정보 페이지에서 스케줄 정보 획득
        data = soup.select('.tip-cover')
        print(type(data), len(data), data[0].contents)
        
        # 콘텐츠 내용에 따라 전처리 => data[0].contents 같은 경우
        db.db_insertCrawlingData(
            tour.title,
            tour.price,
            tour.area,
            data[0].contents,
            keyword
        )
        

# 종료
# 창닫기
driver.close()
driver.quit()
# 프로세스 종료 
import sys
sys.exit()