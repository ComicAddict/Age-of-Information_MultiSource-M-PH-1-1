import numpy as np
import queue as q
import copy
import matplotlib.pyplot as plt
from butools.ph import SamplesFromPH
from butools.ph import ml

sim_time = 100
sim_step = 1000
num_sim = 100
num_src = 3
gen_age = []
gen_peak = []
for i in range(num_src):
    gen_age.append([])
    gen_peak.append([])
    for j in range(sim_time*sim_step):
        gen_age[i].append(0.0)
        gen_peak[i].append(0.0)

num_process = 10*sim_time
p_mode = 3 #1: self, 2: global, 3: priotirized
averages = []

for l in range(num_sim):
    print("Sim %d" % l )
    IAT_list = []
    ST_list = []
    AT_list = []
    ST_Backups = []
    all_arr_times = []
    p = []
    e = []
    r = []
    for i in range(num_src):
        k = 4.0 #this has been in two modes: 2 and 4
        scov_ser = 1.0/k
        rho = 2.0/3.0
        lam = float(i+1)
        mu = lam*k/rho
        if k == 4.0:
            alpha = ml.matrix([[1, 0, 0, 0]])
            S = ml.matrix(
                [[-mu, mu, 0, 0],
                [0, -mu, mu, 0],
                [0, 0, -mu, mu],
                [0, 0, 0, -mu]])
        else:
            alpha = ml.matrix([[1, 0]])
            S = ml.matrix(
                [[-mu, mu],
                [0, -mu]])
        averages.append([])
        p.append([])
        #self preemption
        if p_mode == 1:    
            for j in range(num_src):
                if i ==  j:
                    p[i].append(1.0)
                else:
                    p[i].append(0.0)
        #global preemption
        elif p_mode == 2:
            for j in range(num_src):
                p[i].append(1.0)
        #priotirized preemption
        else:
            for j in range(num_src):
                if i >=  j:
                    p[i].append(1.0)
                else:
                    p[i].append(0.0)
        e.append(0.1)
        r.append(1.0)
        IAT = []
        ST = []
        AT = []
        for j in range(num_process):
            tmp = np.random.exponential(1/lam)*sim_step
            if j == 0:
                IAT.append(0)
            else:
                IAT.append(int(tmp - tmp%1))

        for j in range(num_process):
            tmp = SamplesFromPH(alpha, S, 1)[0]*sim_step
            if not int(tmp - tmp%1) < 1:
                ST.append(int(tmp - tmp%1))

        for j in range(num_process):
            if j == 0:
                AT.append(0)
                all_arr_times.append((0, i, j))
            else:
                AT.append(AT[j-1] + IAT[j])
                all_arr_times.append((AT[j-1] + IAT[j], i, j))
        
        IAT_list.append(IAT)
        ST_list.append(ST)
        AT_list.append(AT)

    ST_Backups = copy.deepcopy(ST_list)
    all_arr_times.sort()

    server_busy = False
    list_age = []
    list_processed = []
    ages = []

    for i in range(num_src):
        ages.append(0)
        list_age.append([])
        list_processed.append([])

    for i in range(sim_time*sim_step):

        if server_busy:
            ST_list[int(current_src)][int(current_prc)] -= 1
            if ST_list[int(current_src)][int(current_prc)] == 0:
                if np.random.uniform() < e[int(current_src)]:
                    #print("%d: Error occured during the transmission of packet %d of source %d" % (i, int(current_spec_prc), int(current_src)))
                    if np.random.uniform() < r[int(current_src)]:
                        ST_list[int(current_src)][int(current_prc)] = ST_Backups[int(current_src)][int(current_prc)]
                        #print("Retransmitting the packet")    
                    else:
                        #print("Packet discarded")    
                        server_busy = False
                else:
                    server_busy = False
                    last_src = 0
                    if(len(list_processed[int(current_src)]) < 1):
                        (arr, dummy, spec_prc) = all_arr_times[int(current_prc)]
                        dec = arr
                    else:
                        last_prc = list_processed[int(current_src)][-1]
                        (arr_now, dummy, spec_prc) = all_arr_times[int(current_prc)]
                        (arr_last, dummy, spec_prc) = all_arr_times[int(last_prc)]
                        dec = arr_now - arr_last + 1
                    list_processed[int(current_src)].append(current_prc)

                    gen_peak[int(current_src)][ages[int(current_src)]] += 1.0
                    ages[int(current_src)] -= dec
                    
                #print("%d: Age of source %d has been decreased by %d" % (i, int(current_src), dec))

        for j in range(num_src):
            gen_age[j][ages[j]] += 1.0/float(num_sim*sim_time*sim_step)
            ages[j] += 1
            #print("Age of source %d is %d" % (j, ages[j]))

        for j in range(num_process):
            (proc_time, proc_src, spec_prc) = all_arr_times[j]
            if i == proc_time:
                #if not qu.full():
                if not server_busy:
                    #qu.put((j, spec_prc, proc_src))
                    (current_prc, current_spec_prc, current_src) = (j, spec_prc, proc_src)
                    server_busy = True
                    #print("%d: Packet %d of Source %d is in the service" % (i, spec_prc, proc_src + 1))
                elif np.random.uniform() < p[current_src][proc_src]:
                    #(preempted_pckt, preempted_spec_pckt, preempted_src) = qu.get()
                    (preempted_pckt, preempted_spec_pckt, preempted_src) = (current_prc, current_spec_prc, current_src)
                    (current_prc, current_spec_prc, current_src) = (j, spec_prc, proc_src)
                    server_busy = True
                    #qu.put((j, spec_prc, proc_src))
                    #print("%d: Packet %d of Source %d preempted packet %d of Source %d" % (i, spec_prc, proc_src + 1, preempted_spec_pckt, preempted_src + 1))

        for j in range(num_src):
            list_age[j].append(ages[j])
    for i in range(num_src):
        averages[i].append(sum(list_age[i])/len(list_age[i]))


plt.ylabel("AoI Process")
plt.xlabel("Time (ms)")

for j in range(num_src):
    age = list_age[j]
    plt.plot([i+1 for i in range(sim_time*sim_step)], gen_age[j], label='Source %d' % (j + 1))
    print("Average age of source %d is %d" % (j+1, sum(averages[j])/len(averages[j])))
    #plt.plot([i+1 for i in range(sim_time*sim_step)], age, label='Source %d' % (j + 1))
    plt.legend()
plt.show()

cdf = []
for i in range(num_src):
    cdf.append([])
    sums = 0
    for j in range(sim_step*sim_time):
        sums += gen_age[i][j]
        cdf[i].append(sums)
    plt.plot([l+1 for l in range(sim_time*sim_step)], cdf[i], label='Source %d' % (i + 1))
    plt.legend()
plt.show()


for i in range(num_src):
    tot = sum(gen_peak[i])
    for j in range(sim_time*sim_step):
        gen_peak[i][j] = gen_peak[i][j]/tot

for j in range(num_src):
    age = list_age[j]
    plt.plot([i+1 for i in range(sim_time*sim_step)], gen_peak[j], label='Source %d' % (j + 1))
    plt.legend()
plt.show()

cdf_peak = []
for i in range(num_src):
    cdf_peak.append([])
    sum = 0
    for j in range(sim_step*sim_time):
        sum += gen_peak[i][j]
        cdf_peak[i].append(sum)
    plt.plot([l+1 for l in range(sim_time*sim_step)], cdf_peak[i], label='Source %d' % (i + 1))
    plt.legend()
plt.show()