# 에디터는 저장소 파일을 직접 고치고 git으로 기록한다. 그래서 git이 필요하다.
FROM python:3.13-alpine

# git: 저장소에 기록한다. 컴파일러: 올라간 코드를 데이터에 직접 돌려 검증한다.
RUN apk add --no-cache git openssh-client build-base openjdk17-jdk

# 채점 현황에서 관리자 API에 없는 테스트 입출력과 컴파일 결과를 DB에서 읽는다.
RUN pip install --no-cache-dir pymysql==1.1.1

WORKDIR /app
COPY app.py /app/app.py
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 컨테이너 안에서 /repo 소유자가 달라도 git이 거부하지 않게 한다.
RUN git config --system --add safe.directory /repo

EXPOSE 8088
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["8088"]
