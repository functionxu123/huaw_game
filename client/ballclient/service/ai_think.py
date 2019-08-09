#encoding:utf-8
'''
Created on Aug 2, 2019

@author: sherl
'''
import ballclient.service.constants as constants
import numpy as np
import random,time

#下面这两个list里面顺序不能动
direction = ['up',  'down',  'left',  'right']
items=['meteor', 'tunnel', 'wormhole', 'power']
wormholes={}#为了方便找到对应的虫洞，这里为  'A':[row, col]
killing_bonus=10
round_change=150
round_believe=6

class one_item:
    def __init__(self, row, col):
        self.row=row
        self.col=col
        self.type=None
        self.extra=None
        self.with_enemy=False
        self.enemyscore=0
        self.last_seen=-round_believe-1
        
    def set_type(self, itype, extra=None):
        #type为类型，另外还要有一个附加的属性记录，如tunnel的方向和waormhole的字母
        self.type=itype
        self.extra=extra
        
    def set_enemy(self, score):
        self.with_enemy=True
        self.enemyscore=int(score)
        
    def update_seen(self, roundid):
        self.last_seen=roundid
        
    def clear_type(self):
        self.type=None
        self.extra=None
        
    def clear_enemy(self):
        self.with_enemy=False
        self.enemyscore=0
        
        
    def get_next2direction(self, row, col, dire, maplen):
        #根据方向计算当前坐标的下一个，附带合理判断
        dire=dire.strip()
        if dire==direction[0]:
            if row<=0: return None
            return [row-1, col]
        elif dire==direction[1]:
            if row>=(maplen-1): return None
            return [row+1, col]
        elif dire==direction[2]:
            if col<=0: return None
            return [row, col-1]
        elif dire==direction[3]:
            if col>=(maplen-1): return None
            return [row, col+1]
        return None
            
        
    def on_movetothis(self, mapitem, killing):
        #当从其他地方挪到本位置上的时候，最终会落到哪里
        #return None:来不到   [row, col]:坐标
        #后一个代表move的收益
        
        if self.type==items[0]:#meteor
            return None,0
        
        elif self.type==items[1]: #'tunnel'
            #if self.on_step_this is not None: return self.on_step_this
            tep=self.get_next2direction(self.row, self.col, self.extra, len(mapitem))
            if tep is None: return tep,0
            return mapitem[tep[0]][tep[1]].on_movetothis(mapitem, killing)
                
        elif self.type==items[2]:#wormhole
            #if self.on_step_this is not None: return self.on_step_this
            ano=self.extra.upper()
            if self.extra.isupper():#if upper char
                ano=self.extra.lower()
            otherside=wormholes[ano]
            
            if self.with_enemy or mapitem[otherside[0] ][ otherside[1]].with_enemy:
                if killing:
                    return otherside,killing_bonus+self.enemyscore+mapitem[otherside[0] ][ otherside[1]].enemyscore
                else:
                    return None, -killing_bonus*3
            return otherside , 0
                
                
        elif self.type==items[3]:#power
            return [self.row, self.col],int(self.extra)
            
        elif self.with_enemy:#enemy
            if killing:
                return [self.row, self.col],killing_bonus+self.enemyscore
            else:
                return None, -killing_bonus*3

        else:#空的
            return [self.row, self.col],0
        
        

class My_ai:
    def __init__(self):
        self.map_shape=[15, 15]   #高和宽
        self.map_game=[]  #地图元素
        self.map_vision=3   #视野大小
        self.map_force='beat'   #think   'beat'
        self.last_enemy={}
        self.killing=False

        
    def set_shape(self, h,w):
        self.map_shape=[int(h), int(w)]  #y,x
        self.map_game=[]
        for i in range(self.map_shape[0]):
            self.map_game.append([])
            for j in range(self.map_shape[1]):
                self.map_game[i].append(one_item(i, j))
    
    def set_vision(self, visi):
        self.map_vision=int(visi)
        
    def set_map_meteor(self, mapstr):
        for i in mapstr:
            x=int(i['x'])
            y=int(i['y'])
            self.map_game[y][x].set_type(items[0])
        
    
    def set_map_tunnel(self, mapstr):
        for i in mapstr:
            x=int(i['x'])
            y=int(i['y'])
            dire=i['direction'].strip()
            self.map_game[y][x].set_type(items[1], dire)
            
            
    
    def set_map_wormhole(self, mapstr):
        global wormholes
        for i in mapstr:
            x=int(i['x'])
            y=int(i['y'])
            name=i['name'].strip()
            self.map_game[y][x].set_type(items[2], name)
            wormholes[name]=[y, x]    #这里为  'A':[row, col]
            
    def set_team(self, teamstr):
        for i in teamstr:
            print i
            teamid=int(i['id'])
            players=i['players']
            force=i['force']
            if teamid==constants.team_id:
                self.map_force=force
            
    def clear(self):
        #换场时的清理
        self.__init__()
        global wormholes
        wormholes={}
    
    def clear_power_enemy_inview(self, row, col, round_id):
        left=max(0, col- self.map_vision)
        right=min(self.map_shape[1], col+self.map_vision+1)
        up=max(0, row-self.map_vision)
        down=min(self.map_shape[0], row+self.map_vision+1)
        for i in range(up, down):
            for j in range(left, right):#清理视野中的power和enemy
                if self.map_game[i][j].type==items[3]: self.map_game[i][j].clear_type()
                if self.map_game[i][j].with_enemy:     self.map_game[i][j].clear_enemy()
                self.map_game[i][j].update_seen(round_id)  #顺便更新下上次看到的信息
                
    def set_power(self, power):
        for i in power:
            x=int(i['x'])
            y=int(i['y'])
            point=int(i['point'])
            self.map_game[y][x].set_type(items[3], point)
            
    def set_enemy(self, enemy_player):
        for i in enemy_player:
            row=enemy_player[i][0]
            col=enemy_player[i][1]
            score=enemy_player[i][2]
            self.map_game[row][col].set_enemy(score)
    
    def on_moveto(self, row, col):
        return self.map_game[row][col].on_movetothis(self.map_game, self.killing)
    
    
    def make_decision(self, my_player, rate, roundid):
        sttime=time.time()
        ret= {}
        for i in my_player:
            plen, path, gain=self.Dijkstra_global_rate(my_player[i][0], my_player[i][1], rate=rate)  #其中rate=1时，完全按照路径
            if np.max(gain)<=0:
                print "no power in sight,random to safe area:"
                mostclose=round_believe
                ind_kep=[random.randint(0, plen.shape[0]-1),  random.randint(0, plen.shape[1]-1)]
                for ii in range(4):#plen.shape[0]
                    for j in range(plen.shape[1]):
                        rand_ind=[random.randint(0, plen.shape[0]-1),  random.randint(0, plen.shape[1]-1)]
                        if gain[rand_ind[0]][rand_ind[1]]>=0 and abs(roundid-self.map_game[rand_ind[0]][rand_ind[1]].last_seen)>=round_believe and abs(plen[rand_ind[0]][rand_ind[1]]-round_believe)<mostclose:
                            mostclose=abs(plen[rand_ind[0]][rand_ind[1]]-round_believe)
                            ind_kep=rand_ind
                _,dire=self.show_path(path, ind_kep[0], ind_kep[1])
                
            else:
                print "heading to area that most gain:"
                mostclose=gain[0][0]
                ind_kep=[0,0]
                for ii in range(plen.shape[0]):
                    for j in range(plen.shape[1]):
                        if gain[ii][j]>mostclose:
                            mostclose=gain[ii][j]
                            ind_kep=[ii, j]
                _,dire=self.show_path(path, ind_kep[0], ind_kep[1])
                
            print "next move:",dire
            ret[i]=dire
        print 'round:',roundid,'->running time:',time.time()-sttime
        return ret
        
    def on_round(self, msg_data):
        my_player={}
        enemy_player={}
        my_all_player={} #这里包括sleep的player
        enemy_all_player={}
        
        self.killing=msg_data['mode']==self.map_force  #是否是优势
        round_id = msg_data['round_id']
        players  = msg_data['players']
        for i in players:
            id=int(i['id'])
            teamid=int(i['team'])
            score=int(i['score'])
            sleep=int(i['sleep'])
            x=int(i['x'])
            y=int(i['y'])
            if teamid==constants.team_id:
                self.clear_power_enemy_inview(y,x, round_id)  #注意这里清理了视野中的能量和敌人，用于刷新视野中的物品
                my_all_player[id]=[y, x, score]
                if not sleep:
                    my_player[id]=[y, x, score]    #以行列保存 [row, col, score]
            else:
                enemy_all_player[id]=[y, x, score]
                if (not sleep):
                    enemy_player[id]=[y, x, score]
        #设置敌人位置，与其他不同，这里是json处理后的一个map
        self.set_enemy(enemy_player)
        #上面已经清理了power。这里只要添上去新的power就行
        if "power" in msg_data: self.set_power(msg_data['power'])
        else: print "round with no power!!"
        
        #到这里本round的地图已经初始化完成
        '''
        self.map_game:地图，包括tunnel,meteor,wormhole,视野中的power
        self.killing:是否为优势
        my_player:我方鲲  id:[row, col, score]
        enemy_player:视野中敌方鲲
        '''
        ret={}
        if (self.killing and round_id<round_change-5):
            #一开始时为优势
            ret= self.make_decision(my_player, 0.5, round_id)  #其中rate=1时，完全按照路径
 
        elif self.killing and round_id>=round_change:
            #后面的优势,抓人
            ret= self.make_decision(my_player, 0.8, round_id)
        elif not self.killing and round_id<round_change:
            #前面为劣势，吃分
            ret= self.make_decision(my_player, 0.2, round_id)
        else:
            #后面是劣势，逃命
            ret= self.make_decision(my_player, 0.4, round_id)

        print ret
        self.last_enemy=enemy_player
        return ret
        
    def Dijkstra_global_rate(self, startrow, startcol, rate=1.0):
        #按比例来计算路径长与power的和，得到最优解，其中rate=1时，完全按照路径，rate=0时完全按照power
        sttime=time.time()
        print "start once DJ algo cal:"
        max_val=10000
        
        kep=np.ones(self.map_shape, dtype=np.int32)*max_val
        use=np.zeros(self.map_shape, dtype=np.int8)
        path=np.ones([self.map_shape[0], self.map_shape[1],3], dtype=np.int32)*(-1)  #该点前一点的坐标及前一点得到该点的移动方向
        power_gain=np.ones(self.map_shape, dtype=np.int32)*(-max_val)  #power初始化为负数，因为其应往较大处发展
        
        kep[startrow][startcol]=0  #这里是两个初始化
        power_gain[startrow][startcol]=0
        
        for i in range(self.map_shape[0]*self.map_shape[1]):
            min_tep=max_val
            for k in range(self.map_shape[0]):
                for l in range(self.map_shape[1]):
                    if not use[k][l] and kep[k][l]*rate-power_gain[k][l]*(1-rate)  < min_tep:
                        min_tep=kep[k][l]*rate-power_gain[k][l]*(1-rate)
                        ind_kep=[k, l]
            use[ind_kep[0]][ind_kep[1]]=1
            
            print "h*w finding:",ind_kep,min_tep
            #已经无法继续了
            if min_tep>=max_val-1: break
            #update
            #up
            if ind_kep[0]>0 and (not use[ind_kep[0]-1][ind_kep[1]]):
                print "up",":on moving to:",[ind_kep[0]-1, ind_kep[1]]
                move_ind,gain=self.on_moveto(ind_kep[0]-1, ind_kep[1])
                print move_ind,gain
                if move_ind is not None :#里面
                    if kep[move_ind[0]][move_ind[1]]*rate-(1-rate)*power_gain[move_ind[0]][move_ind[1]]>rate*(kep[ind_kep[0]][ind_kep[1]]+1)-(1-rate)*(power_gain[ind_kep[0]][ind_kep[1]]+gain):
                        kep[move_ind[0]][move_ind[1]]=kep[ind_kep[0]][ind_kep[1]]+1
                        path[move_ind[0]][move_ind[1]][0:2]=ind_kep
                        path[move_ind[0]][move_ind[1]][2]=0
                        power_gain[move_ind[0]][move_ind[1]]=power_gain[ind_kep[0]][ind_kep[1]]+gain
            #down
            if ind_kep[0]<self.map_shape[0]-1 and (not use[ind_kep[0]+1][ind_kep[1]]):
                print "down",":on moving to:",[ind_kep[0]+1, ind_kep[1]]
                move_ind,gain=self.on_moveto(ind_kep[0]+1, ind_kep[1])
                print move_ind,gain
                if move_ind is not None :#里面
                    if kep[move_ind[0]][move_ind[1]]*rate-(1-rate)*power_gain[move_ind[0]][move_ind[1]]>rate*(kep[ind_kep[0]][ind_kep[1]]+1)-(1-rate)*(power_gain[ind_kep[0]][ind_kep[1]]+gain):
                        kep[move_ind[0]][move_ind[1]]=kep[ind_kep[0]][ind_kep[1]]+1
                        path[move_ind[0]][move_ind[1]][0:2]=ind_kep
                        path[move_ind[0]][move_ind[1]][2]=1
                        power_gain[move_ind[0]][move_ind[1]]=power_gain[ind_kep[0]][ind_kep[1]]+gain       
            #left
            if ind_kep[1]>0 and (not use[ind_kep[0]][ind_kep[1]-1]):
                print "left",":on moving to:",[ind_kep[0], ind_kep[1]-1]
                move_ind,gain=self.on_moveto(ind_kep[0], ind_kep[1]-1)
                print move_ind,gain
                if move_ind is not None :#里面
                    if kep[move_ind[0]][move_ind[1]]*rate-(1-rate)*power_gain[move_ind[0]][move_ind[1]]>rate*(kep[ind_kep[0]][ind_kep[1]]+1)-(1-rate)*(power_gain[ind_kep[0]][ind_kep[1]]+gain):
                        kep[move_ind[0]][move_ind[1]]=kep[ind_kep[0]][ind_kep[1]]+1
                        path[move_ind[0]][move_ind[1]][0:2]=ind_kep
                        path[move_ind[0]][move_ind[1]][2]=2
                        power_gain[move_ind[0]][move_ind[1]]=power_gain[ind_kep[0]][ind_kep[1]]+gain         
            #right
            if ind_kep[1]<self.map_shape[1]-1 and (not use[ind_kep[0]][ind_kep[1]+1]):
                print "right",":on moving to:",[ind_kep[0], ind_kep[1]+1]
                move_ind,gain=self.on_moveto(ind_kep[0], ind_kep[1]+1)
                print move_ind,gain
                if move_ind is not None :#里面
                    if kep[move_ind[0]][move_ind[1]]*rate-(1-rate)*power_gain[move_ind[0]][move_ind[1]]>rate*(kep[ind_kep[0]][ind_kep[1]]+1)-(1-rate)*(power_gain[ind_kep[0]][ind_kep[1]]+gain):
                        kep[move_ind[0]][move_ind[1]]=kep[ind_kep[0]][ind_kep[1]]+1
                        path[move_ind[0]][move_ind[1]][0:2]=ind_kep
                        path[move_ind[0]][move_ind[1]][2]=3
                        power_gain[move_ind[0]][move_ind[1]]=power_gain[ind_kep[0]][ind_kep[1]]+gain
        
        print "once DJ algothim time:",time.time()-sttime
        #process path
        return kep, path, power_gain
        
        
        
    def Dijkstra_global_path(self, startrow, startcol):
        max_val=10000
        kep=np.ones(self.map_shape)*max_val
        use=np.zeros(self.map_shape)
        path=np.ones([self.map_shape[0], self.map_shape[1],3])*(-1)  #该点前一点的坐标及前一点得到该点的移动方向
        power_gain=np.zeros(self.map_shape)
        
        kep[startrow][startcol]=0
        for i in range(self.map_shape[0]*self.map_shape[1]):
            min_tep=max_val
            for k in range(self.map_shape[0]):
                for l in range(self.map_shape[1]):
                    if not use[k][l] and kep[k][l]<min_tep:
                        min_tep=kep[k][l]
                        ind_kep=[k, l]
            use[ind_kep[0]][ind_kep[1]]=1
            #已经无法继续了
            if min_tep>=max_val: break
            #update
            #up
            if ind_kep[0]>0 and (not use[ind_kep[0]-1][ind_kep[1]]):
                move_ind,gain=self.on_moveto(ind_kep[0]-1, ind_kep[1])
                if move_ind is not None :#里面
                    if kep[move_ind[0]][move_ind[1]]>min_tep+1:
                        kep[move_ind[0]][move_ind[1]]=min_tep+1
                        path[move_ind[0]][move_ind[1]][0:2]=ind_kep
                        path[move_ind[0]][move_ind[1]][2]=0
                        power_gain[move_ind[0]][move_ind[1]]=power_gain[ind_kep[0]][ind_kep[1]]+gain
            #down
            if ind_kep[0]<self.map_shape[0]-1 and (not use[ind_kep[0]+1][ind_kep[1]]):
                move_ind,gain=self.on_moveto(ind_kep[0]+1, ind_kep[1])
                if move_ind is not None :#里面
                    if kep[move_ind[0]][move_ind[1]]>min_tep+1:
                        kep[move_ind[0]][move_ind[1]]=min_tep+1
                        path[move_ind[0]][move_ind[1]][0:2]=ind_kep
                        path[move_ind[0]][move_ind[1]][2]=1           
                        power_gain[move_ind[0]][move_ind[1]]=power_gain[ind_kep[0]][ind_kep[1]]+gain       
            #left
            if ind_kep[1]>0 and (not use[ind_kep[0]][ind_kep[1]-1]):
                move_ind,gain=self.on_moveto(ind_kep[0], ind_kep[1]-1)
                if move_ind is not None :#里面
                    if kep[move_ind[0]][move_ind[1]]>min_tep+1:
                        kep[move_ind[0]][move_ind[1]]=min_tep+1
                        path[move_ind[0]][move_ind[1]][0:2]=ind_kep
                        path[move_ind[0]][move_ind[1]][2]=2          
                        power_gain[move_ind[0]][move_ind[1]]=power_gain[ind_kep[0]][ind_kep[1]]+gain         
            #right
            if ind_kep[1]<self.map_shape[1]-1 and (not use[ind_kep[0]][ind_kep[1]+1]):
                move_ind,gain=self.on_moveto(ind_kep[0], ind_kep[1]+1)
                if move_ind is not None :#里面
                    if kep[move_ind[0]][move_ind[1]]>min_tep+1:
                        kep[move_ind[0]][move_ind[1]]=min_tep+1
                        path[move_ind[0]][move_ind[1]][0:2]=ind_kep
                        path[move_ind[0]][move_ind[1]][2]=3
                        power_gain[move_ind[0]][move_ind[1]]=power_gain[ind_kep[0]][ind_kep[1]]+gain
        
        #process path
        return kep, path, power_gain
            
    
        
    def Dijkstra_local_path(self, startrow, startcol, endrow, endcol):
        max_val=10000
        #由输入保证作坐标合理性
        w=abs(endcol-startcol)+1
        h=abs(endrow-startrow)+1
        
        kep=np.ones([h, w])*max_val
        use=np.zeros([h, w])
        path=np.ones([h,w,3])*(-1)  #该点前一点的坐标及前一点得到该点的移动方向
        
        row_st=startrow-min(endrow, startrow)
        col_st=startcol-min(endcol, startcol)
        
        row_end=endrow-min(endrow, startrow)
        col_end=endcol-min(endcol, startcol)
        
        kep[row_st][col_st]=0
        
        for i in range(h*w):
            #先找到min值和坐标
            min_tep=max_val
            for k in range(h):
                for l in range(w):
                    if not use[k][l] and kep[k][l]<min_tep:
                        min_tep=kep[k][l]
                        ind_kep=[k, l]
            use[ind_kep[0]][ind_kep[1]]=1
            #已经无法继续了
            if min_tep>=max_val: break
            #update
            #up
            if ind_kep[0]>0 and (not use[ind_kep[0]-1][ind_kep[1]]):
                move_ind,gain=self.on_moveto(min(endrow, startrow)+ind_kep[0]-1, min(endcol, startcol)+ind_kep[1])
                if move_ind is not None and move_ind[0]>=min(endrow, startrow) and move_ind[1]<=max(endrow, startrow) and move_ind[1]>=min(endcol, startcol) and move_ind[1]<=max(endcol, startcol):#矩形里面
                    if kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]>min_tep+1:
                        kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]=min_tep+1
                        path[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)][0:2]=ind_kep
                        path[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)][2]=0
            #down
            if ind_kep[0]<h-1 and (not use[ind_kep[0]+1][ind_kep[1]]):
                move_ind,gain=self.on_moveto(min(endrow, startrow)+ind_kep[0]+1, min(endcol, startcol)+ind_kep[1])
                if move_ind is not None and move_ind[0]>=min(endrow, startrow) and move_ind[1]<=max(endrow, startrow) and move_ind[1]>=min(endcol, startcol) and move_ind[1]<=max(endcol, startcol):#矩形里面
                    if kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]>min_tep+1:
                        kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]=min_tep+1    
                        path[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)][0:2]=ind_kep    
                        path[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)][2]=1                    
            #left
            if ind_kep[1]>0 and (not use[ind_kep[0]][ind_kep[1]-1]):
                move_ind,gain=self.on_moveto(min(endrow, startrow)+ind_kep[0], min(endcol, startcol)+ind_kep[1]-1)
                if move_ind is not None and move_ind[0]>=min(endrow, startrow) and move_ind[1]<=max(endrow, startrow) and move_ind[1]>=min(endcol, startcol) and move_ind[1]<=max(endcol, startcol):#矩形里面
                    if kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]>min_tep+1:
                        kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]=min_tep+1         
                        path[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)][0:2]=ind_kep
                        path[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)][2]=2                   
            #right
            if ind_kep[1]<w-1 and (not use[ind_kep[0]][ind_kep[1]+1]):
                move_ind,gain=self.on_moveto(min(endrow, startrow)+ind_kep[0], min(endcol, startcol)+ind_kep[1]+1)
                if move_ind is not None and move_ind[0]>=min(endrow, startrow) and move_ind[1]<=max(endrow, startrow) and move_ind[1]>=min(endcol, startcol) and move_ind[1]<=max(endcol, startcol):#矩形里面
                    if kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]>min_tep+1:
                        kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]=min_tep+1
                        path[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)][0:2]=ind_kep
                        path[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)][2]=3
        
        #process path
        
    def show_path(self, path, endrow, endcol):
        #path为[h, w, 3]的矩阵，3 is [pre_row, pre_col, pre_direction]
        ret=np.zeros(path.shape[:2]  ,dtype=np.int8)
        tep=[endrow, endcol]
        dire=direction[random.randint(0, 3)]
        while tep[0]>=0 and tep[0]<path.shape[0] and tep[1]<path.shape[1] and tep[1]>=0:
            ret[tep[0]][tep[1]]=1
            if path[tep[0]][tep[1]][2]>=0:
                dire=direction[path[tep[0]][tep[1]][2]]
            tep=path[tep[0]][tep[1]][:2]
        return ret,dire
        
    
        
        



if __name__ == '__main__':
    AI=My_ai()
    AI.set_shape(6, 6)
    AI.set_map_meteor([{'x':2, 'y':2},
                       {'x':3, 'y':2},
                       {'x':4, 'y':2},
                       {'x':4, 'y':1}])
    #AI.set_map_tunnel
    #
    AI.set_power([{'x':1, 'y':3, 'point':2},
                  {'x':2, 'y':3, 'point':1},
                  {'x':2, 'y':1, 'point':2},
                  {'x':2, 'y':0, 'point':3},
                  {'x':3, 'y':0, 'point':2},
                  {'x':4, 'y':0, 'point':4},
                  {'x':5, 'y':0, 'point':5},
                  {'x':1, 'y':0, 'point':3},
                  {'x':1, 'y':2, 'point':3},])
    
    plen, path, gain=AI.Dijkstra_global_rate(2, 0, rate=0.5)  #其中rate=1时，完全按照路径，rate=0时完全按照power

    print plen
    print AI.show_path(path, 2, 5)
    print gain
    








