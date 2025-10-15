# Pain Points
1. How the secret resolve is working now is security hazard, seriously have change the working of it, so no code injection can be done
2. NPU is al securtity hazrad beacuse they execute remote code, but it can solved easyly beacuse we can use firework kinda system which make more isolated vm and we can also restric the out going connections 
3. we should rewite the whole NodeRunner and NPU blocks in golang and use and new monitoring system
