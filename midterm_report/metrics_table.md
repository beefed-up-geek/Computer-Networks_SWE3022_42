| 시나리오 | 링크 조건 | 평균 처리량 (Mbps) | 관찰 포인트 |
| --- | --- | --- | --- |
| Scenario 1 – Slow Start & AIMD | h1—s1—h2 · bw=10 Mbps · delay=30 ms · queue=100 | 9.49 | Slow start 이후 선형 증가, 손실 시 cwnd 절반 감소 |
| Scenario 2 – Random Loss Misinterpretation | h1—s1—h2 · bw=10 Mbps · delay=20 ms · loss=5% | 0.40 | 비혼잡 손실에도 Reno가 감속 → 평균 처리량 급락 |
| Scenario 3 – High BDP Path | h1—s1—h2 · bw=100 Mbps · delay=150 ms · queue=2000 | 89.98 | RTT↑ 환경에서 선형 증가 속도가 느려 파이프 미충족 |
| Scenario 4 – RTT Unfairness | h1/h3—s1—h2 · (h1:10 ms, h3:100 ms) · bw=20 Mbps | h1: 12.28 / h3: 7.07 (Jain 0.93) | 짧은 RTT 흐름이 대역폭 대부분 획득, Jain 지수 0.93 |
| Scenario 5 – Bufferbloat & Fast Recovery | h1—s1—h2 · bw=10 Mbps · delay=20 ms · queue=2000 | 9.52 | 크게 부푼 큐로 RTT 급증, Fast Retransmit/Recovery 반복 |
