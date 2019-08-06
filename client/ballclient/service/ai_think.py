#encoding:utf-8
'''
Created on Aug 2, 2019

@author: sherl
'''
import ballclient.service.constants as constants
import numpy as np

#下面这两个list里面顺序不能动
direction = ['up',  'down',  'left',  'right']
items=['meteor', 'tunnel', 'wormhole', 'power', 'enemy']
wormholes={}#为了方便找到对应的虫洞，这里为  'A':[row, col]
killing_bonus=10
round_change=150

class one_item:
    def __init__(self, row, col):
        self.row=row
        self.col=col
        self.type=None
        self.extra=None
        
    def set_type(self, itype, extra=None):
        #type为类型，另外还要有一个附加的属性记录，如tunnel的方向和waormhole的字母
        self.type=itype
        self.extra=extra
        
    def clear_type(self):
        self.type=None
        self.extra=None
        
        
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
            return mapitem[tep[0], tep[1]].on_movetothis(mapitem)
                
        elif self.type==items[2]:#wormhole
            #if self.on_step_this is not None: return self.on_step_this
            ano=self.extra.upper()
            if self.extra.isupper():#if upper char
                ano=self.extra.lower()
            
            return wormholes[ano],0
                
        elif self.type==items[3]:#power
            return [self.row, self.col],int(self.extra)
            
        elif self.type==items[4]:#enemy
            if killing:
                return [self.row, self.col],killing_bonus
            else:
                return None, -killing_bonus

        else:#空的
            return [self.row, self.col],0
        
        

class My_ai:
    def __init__(self):
        self.map_shape=[]   #高和宽
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
            dire=i('direction').strip()
            self.map_game[y][x].set_type(items[1], dire)
            
            
    
    def set_map_wormhole(self, mapstr):
        global wormholes
        for i in mapstr:
            x=int(i['x'])
            y=int(i['y'])
            name=i('name').strip()
            self.map_game[y][x].set_type(items[2], name)
            wormholes[name]=[y, x]    #这里为  'A':[row, col]
            
    def set_team(self, teamstr):
        for i in teamstr:
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
    
    def clear_power_enemy_inview(self, row, col):
        left=max(0, col- self.map_vision)
        right=min(self.map_shape[1], col+self.map_vision+1)
        up=max(0, row-self.map_vision)
        down=min(self.map_shape[0], row+self.map_vision+1)
        for i in range(up, down):
            for j in range(left, right):#清理视野中的power和enemy
                if self.map_game[i][j].type==items[3] or self.map_game[i][j].type==items[4]:  self.map_game[i][j].clear_type()
                
    def set_power(self, power):
        for i in power:
            x=int(i['x'])
            y=int(i['y'])
            point=int(i['point'])
            self.map_game[y][x].set_type(items[3], point)
    
    def on_moveto(self, row, col):
        return self.map_game[row][col].on_movetothis(self.map_game, self.killing)
        
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
                self.clear_power_enemy_inview(y,x)  #注意这里清理了视野中的能量和敌人，用于刷新视野中的物品
                my_all_player[id]=[y, x, score]
                if not sleep:
                    my_player[id]=[y, x, score]    #以行列保存 [row, col, score]
            else:
                enemy_all_player[id]=[y, x, score]
                if (not sleep):
                    enemy_player[id]=[y, x, score]
        #设置敌人位置，与其他不同，这里是json处理后的一个map
        #self.set_enemy(enemy_player)
        #上面已经清理了power。这里只要添上去新的power就行
        self.set_power(msg_data['power'])
        
        #到这里本round的地图已经初始化完成
        '''
        self.map_game:地图，包括tunnel,meteor,wormhole,视野中的power
        self.killing:是否为优势
        my_player:我方鲲  id:[row, col, score]
        enemy_player:视野中敌方鲲
        '''
        if self.killing and round_id<round_change-5:
            #一开始时为优势
            pass
        elif self.killing and round_id>=round_change:
            #后面的优势,抓人
            pass
        elif not self.killing and round_id<round_change:
            #前面为劣势，吃分
            pass
        else:
            #后面是劣势，逃命
            pass
        
        self.last_enemy=enemy_player
        
    def Dijkstra_power(self, startrow, startcol, endrow, endcol):
        max_val=10000
        #由输入保证作坐标合理性
        w=abs(endcol-startcol)+1
        h=abs(endrow-startrow)+1
        forward_row=1
        if startrow>endrow:
            forward_row=-1
        forward_col=1
        if startcol>endcol:
            forward_col=-1
            
        kep=np.ones([h, w])*max_val
        use=np.zeros([h, w])
        row_st=startrow-min(endrow, startrow)
        col_st=startcol-min(endcol, startcol)
        
        kep[row_st][col_st]=0
        
        for i in range(h):
            for j in range(w):
                
                min_tep=max_val
                for k in range(h):
                    for l in range(w):
                        if not use[k][l] and kep[k][l]<min_tep:
                            min_tep=kep[k][l]
                            ind_kep=[k, l]
                use[ind_kep[0]][ind_kep[1]]=1
                #update
                #up
                if ind_kep[0]>0 and (not use[ind_kep[0]-1][ind_kep[1]]):
                    move_ind,gain=self.on_moveto(min(endrow, startrow)+ind_kep[0]-1, min(endcol, startcol)+ind_kep[1])
                    if move_ind[0]>=min(endrow, startrow) and move_ind[1]<=max(endrow, startrow) and move_ind[1]>=min(endcol, startcol) and move_ind[1]<=max(endcol, startcol):#矩形里面
                        if kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]>min_tep+1:
                            kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]=min_tep+1
                #down
                if ind_kep[0]<h-1 and (not use[ind_kep[0]+1][ind_kep[1]]):
                    move_ind,gain=self.on_moveto(min(endrow, startrow)+ind_kep[0]+1, min(endcol, startcol)+ind_kep[1])
                    if move_ind[0]>=min(endrow, startrow) and move_ind[1]<=max(endrow, startrow) and move_ind[1]>=min(endcol, startcol) and move_ind[1]<=max(endcol, startcol):#矩形里面
                        if kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]>min_tep+1:
                            kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]=min_tep+1                            
                #left
                if ind_kep[1]>0 and (not use[ind_kep[0]][ind_kep[1]-1]):
                    move_ind,gain=self.on_moveto(min(endrow, startrow)+ind_kep[0], min(endcol, startcol)+ind_kep[1]-1)
                    if move_ind[0]>=min(endrow, startrow) and move_ind[1]<=max(endrow, startrow) and move_ind[1]>=min(endcol, startcol) and move_ind[1]<=max(endcol, startcol):#矩形里面
                        if kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]>min_tep+1:
                            kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]=min_tep+1                            
                #right
                if ind_kep[1]<w-1 and (not use[ind_kep[0]][ind_kep[1]+1]):
                    move_ind,gain=self.on_moveto(min(endrow, startrow)+ind_kep[0], min(endcol, startcol)+ind_kep[1]+1)
                    if move_ind[0]>=min(endrow, startrow) and move_ind[1]<=max(endrow, startrow) and move_ind[1]>=min(endcol, startcol) and move_ind[1]<=max(endcol, startcol):#矩形里面
                        if kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]>min_tep+1:
                            kep[move_ind[0]-min(endrow, startrow)][move_ind[1]-min(endcol, startcol)]=min_tep+1
                            
                        
                
        
        
        
        
    #各自实现
    def kill_atfirst(self):
        pass
    
    def kill_atlast(self):
        pass
    def run_atfirst(self):
        pass
    def run_atlast(self):
        pass
        
        



if __name__ == '__main__':
    pass








