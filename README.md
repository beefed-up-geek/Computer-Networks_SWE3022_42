# 🧠 Programming Assignment  
## Improving the Performance of TCP Reno Algorithm  
**마감일:** 2025년 12월 12일  

---

## 🗂 1쪽 – 표지
- **제목:** *Programming Assignment – Improving the Performance of TCP Reno Algorithm*  
- **제출 마감일:** 2025년 12월 12일  
- **주제:**  
  - Linux 커널에 구현된 TCP 혼잡 제어 알고리즘 중 하나인 **TCP Reno**의 성능을 개선하는 과제  

---

## 📘 2쪽 – Assignment Overview (과제 개요)
### 🎯 목표
- Linux Kernel에 포함된 TCP 혼잡 제어 알고리즘 **Reno**를 수정(refactor/modify)하여  
  성능을 향상시키고, 실험을 통해 결과를 분석한다.

### 🧩 실행 환경
- **운영체제:** Ubuntu 20.04 LTS (VM 기반)  
- **네트워크 설정:**  
  - 연결 수: 10개  
  - 대역폭(Throughput): 1 Mbps  
  - 왕복 지연시간(RTT): 200 ms  
- **분석 지표:** Fairness(공정성), Link Utilization(링크 활용률), Congestion Control(혼잡 제어 성능)

---

## 🧾 3쪽 – Assignment Explanation (1)
### 📍 세부 목표
- 특정 네트워크 환경에서 **TCP Reno의 문제점**을 분석하고,  
  알고리즘을 **수정/리팩터링**하여 성능을 개선한 후 실험 및 결과 분석을 수행한다.

### ⚙️ 수행 절차
1. 네트워크 환경 설정  
2. 기존 Reno 성능 측정  
3. Reno 알고리즘 수정  
4. 수정된 Reno 성능 측정  
5. 결과 분석 및 보고서 작성  

### 💡 코드 작성 관련
- **권장:** 제공된 `reno_custom.c` 사용  
- **선택:** `/net/ipv4/tcp_cong.c` 직접 수정 가능

---

## 🌐 4쪽 – Assignment Explanation (2)
### 🧱 자유롭게 설정 가능한 네트워크 조건 예시
- 10~1000개의 동시 TCP 연결  
- 고대역폭(high bandwidth) 및 고지연(high latency) 환경  
- 링크 오류로 인한 높은 패킷 손실률 환경  
- 지터(Jitter)가 큰 네트워크 환경  

### 📊 실험 비교 방식
- 수정된 알고리즘과 기존 Reno를 단일 환경에서 비교해도 충분  
- 여러 조건에서 **강건성(Robustness)** 분석 시 가산점 부여  

### ⚖️ 공정성 실험 요건
- 최소 **5개 이상의 TCP 연결**로 실험을 수행해야 함  

---

## 📈 5쪽 – Assignment Explanation (3)
### 🚀 TCP 성능 평가 지표
- 필수 측정 항목:
  - **Link Utilization (링크 활용률)**  
  - **Fairness (공정성)**  
  - **Latency (지연 시간)**  
- 필요 시 추가 네트워크 지표를 사용 가능  

> ⚠️ 모든 지표가 반드시 개선될 필요는 없으며, 일부 항목만 개선되어도 무방함.

---

## 🧮 6쪽 – Assignment Explanation (4): 제출물 구성
### 📝 1. 중간 보고서 (Intermediate Report)
- 형식: 자유 형식  
- 내용: 제출 시점까지의 진행 상황  
- 제출 형식: PDF  
- 평가: 점수에 직접 반영되지 않음  

### 📘 2. 최종 보고서 (Final Report)
- 분량: **최소 6페이지 이상** (상한 없음)  
- 작성 도구: Word 또는 한컴  
- 제출 형식: PDF  
- 포함 내용:
  1. 설정한 문제 상황 및 기존 Reno의 실험 결과  
  2. 문제 해결 전략  
  3. 수정된 TCP Reno 알고리즘 설명  
  4. 성능 평가 및 분석  

### 💻 3. C 코드 (Final)
- `/net/ipv4/tcp_cong.c`를 기반으로 한 개선 코드 제출  
- 참고: `reno_custom.c` (가이드 36쪽)

---

## ⏰ 7쪽 – Assignment Explanation (5): 마감 및 감점 규정
### 📅 마감일
| 구분 | 마감일시 | 제출 내용 |
|------|------------|-----------|
| **중간 보고서** | 2025/10/31 23:59 | Report only |
| **최종 보고서 + 코드** | 2025/12/12 23:59 | Report + Code |

### ⚠️ 지각 제출 시 감점
- 하루 지연 시 **25% 감점**
- 3일 초과 시 **미제출(0점) 처리**

### 💯 예시 (기준점수 80점)
| 제출일 | 감점 후 점수 |
|---------|---------------|
| 12/13 | 60점 |
| 12/14 | 40점 |
| 12/15 이후 | 0점 (미제출 처리) |

---
