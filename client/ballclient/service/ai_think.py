#encoding:utf-8
'''
Created on Aug 2, 2019

@author: sherl
'''
import ballclient.service.constants as constants

#下面这两个list里面顺序不能动
direction = ['up',  'down',  'left',  'right']
items=['meteor', 'tunnel', 'wormhole', 'power', 'enemy']
wormholes={}#为了方便找到对应的虫洞，这里为  'A':[row, col]
killing_bonus=10

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
        
        
    def on_round(self, msg_data):
        my_player={}
        enemy_player={}
        
        killing=msg_data['mode']==self.map_force  #是否是优势
        round_id = msg_data['round_id']
        players  = msg_data['players']
        for i in players:
            id=int(i['id'])
            teamid=int(i['team'])
            score=int(i['score'])
            sleep=int(i['sleep'])
            x=int(i['x'])
            y=int(i['y'])
            if teamid==constants.team_id and (not sleep):
                my_player[id]=[y, x, score]    #以行列保存 [row, col, score]
            elif teamid!=constants.team_id and (not sleep):
                enemy_player[id]=[y, x, score]
        
        power=msg_data['power']
        for i in power:
            x=int(i['x'])
            y=int(i['y'])
            point=int(i['point'])
            




if __name__ == '__main__':
    pass








