import pickle
import cv2
import time
import sys
import random

import numpy as np
from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer

from map import update_map

class SerralBot(BotAI):
    async def on_step(self, iteration):
        action = None
        while action is None:
            try:
                with open('state_rwd_action.pkl', 'rb') as f:
                    state_rwd_action = pickle.load(f)

                    if state_rwd_action['action'] is not None:
                        action = state_rwd_action['action']
            except:
                pass

        if iteration == 0:
            await self.chat_send("(glhf)")

        await self.distribute_workers() # put idle workers back to work
        
        if not self.townhalls.ready:
            # Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
            for worker in self.workers:
                worker.attack(self.enemy_start_locations[0])
            return

        '''
        0: expand (ie: move to next spot, or build to 16 (minerals)+3 assemblers+3)
        1: build stargate (or up to one) (evenly)
        2: build voidray (evenly)
        3: send scout (evenly/random/closest to enemy?)
        4: attack (known buildings, units, then enemy base, just go in logical order.)
        5: voidray flee (back to base)
        '''
        # 0: expand (ie: move to next spot, or build to 16 (minerals)+3 assemblers+3)
        if action == 0:
            try:
                nexus = self.townhalls.ready.random

                if self.supply_left < 4:
                    # build pylons. 
                    if self.already_pending(UnitTypeId.PYLON) == 0:
                        if self.can_afford(UnitTypeId.PYLON):
                            await self.build(UnitTypeId.PYLON, near=nexus)

                # build probes until we have 22 total:
                worker_count = len(self.workers.closer_than(10, nexus))
                if worker_count < 22: # 16+3+3
                    if nexus.is_idle and self.can_afford(UnitTypeId.PROBE):
                        nexus.train(UnitTypeId.PROBE)

                # build assimilators:
                for vg in self.vespene_geyser.closer_than(15, nexus):
                    # build assimilator if there isn't one already:
                    if not self.can_afford(UnitTypeId.ASSIMILATOR):
                        break
                    worker = self.select_build_worker(vg.position)
                    if worker is None:
                        break

                    if not self.gas_buildings or not self.gas_buildings.closer_than(2, vg).exists:
                        worker.build_gas(vg)
                        worker.stop(queue=True)

                if self.already_pending(UnitTypeId.NEXUS) == 0 and self.can_afford(UnitTypeId.NEXUS):
                    await self.expand_now()
            except Exception as e:
                print(e)


        #1: build stargate (or up to one) (evenly)
        elif action == 1:
            nexus = self.townhalls.ready.random

            try:
                # is there is not a gateway close:
                if not self.structures(UnitTypeId.GATEWAY).closer_than(10, nexus).exists:
                    # if we can afford it:
                    if self.can_afford(UnitTypeId.GATEWAY) and self.already_pending(UnitTypeId.GATEWAY) == 0:
                        # build gateway
                        await self.build(UnitTypeId.GATEWAY, near=nexus)
                    
                # if there is not a cybernetics core close:
                if not self.structures(UnitTypeId.CYBERNETICSCORE).closer_than(10, nexus).exists:
                    # if we can afford it:
                    if self.can_afford(UnitTypeId.CYBERNETICSCORE) and self.already_pending(UnitTypeId.CYBERNETICSCORE) == 0:
                        # build cybernetics core
                        await self.build(UnitTypeId.CYBERNETICSCORE, near=nexus)

                # if there is not a stargate close:
                if not self.structures(UnitTypeId.STARGATE).closer_than(10, nexus).exists:
                    # if we can afford it:
                    if self.can_afford(UnitTypeId.STARGATE) and self.already_pending(UnitTypeId.STARGATE) == 0:
                        # build stargate
                        await self.build(UnitTypeId.STARGATE, near=nexus)
            except Exception as e:
                print(e)


        #2: build voidray (random stargate)
        elif action == 2:
            try:
                if self.can_afford(UnitTypeId.VOIDRAY):
                    for sg in self.structures(UnitTypeId.STARGATE).ready.idle:
                        if self.can_afford(UnitTypeId.VOIDRAY):
                            sg.train(UnitTypeId.VOIDRAY)
            except Exception as e:
                print(e)

        #3: send scout
        elif action == 3:
            try:
                self.last_sent
            except:
                self.last_sent = 0

            # prevent bot from scouting too often
            if (iteration - self.last_sent) > 200:
                try:
                    if self.units(UnitTypeId.PROBE).idle.exists:
                        # pick one of these randomly:
                        probe = self.units(UnitTypeId.PROBE).idle.random
                    else:
                        probe = self.units(UnitTypeId.PROBE).random
                    # send probe towards enemy base:
                    probe.attack(self.enemy_start_locations[0])
                    self.last_sent = iteration

                except Exception as e:
                    pass


        #4: attack (known buildings, units, then enemy base, just go in logical order.)
        elif action == 4:
            try:
                # take all void rays and attack!
                for vr in self.units(UnitTypeId.VOIDRAY).idle:
                    targets = (self.enemy_units | self.enemy_structures).filter(lambda unit: unit.can_be_attacked)
                    if targets:
                        target = targets.closest_to(vr)
                        vr.attack(target)
                    else:
                        vr.attack(self.enemy_start_locations[0])
            except Exception as e:
                print(e)
            

        #5: voidray flee (back to base)
        elif action == 5:
            if self.units(UnitTypeId.VOIDRAY).amount > 0:
                for vr in self.units(UnitTypeId.VOIDRAY):
                    vr.attack(self.start_location)

        # update map
        map = update_map(self)

        # reward function:
        reward = 0
        try:
            attack_count = 0
            # iterate through our void rays:
            for voidray in self.units(UnitTypeId.VOIDRAY):
                # if voidray is attacking and is in range of enemy unit:
                if voidray.is_attacking and voidray.target_in_range:
                    if self.enemy_units.closer_than(8, voidray) or self.enemy_structures.closer_than(8, voidray):
                        # reward += 0.005 # original was 0.005, decent results, but let's 3x it. 
                        reward += 0.015  
                        attack_count += 1
        except Exception as e:
            print("Reward Exception:", str(e))
            reward = 0

        # write the file: 
        data = {"state": map, "reward": reward, "action": None, "terminated": False}  # empty action waiting for the next one!
        with open('state_rwd_action.pkl', 'wb') as f:
            pickle.dump(data, f)
        if iteration % 100 == 0:
            print(f"Iter: {iteration}. RWD: {reward}. VR: {self.units(UnitTypeId.VOIDRAY).amount}")


result = run_game(
    maps.get("AbyssalReefLE"),
    [Bot(Race.Protoss, SerralBot()),
        Computer(Race.Zerg, Difficulty.Hard)],
    realtime=False,
)

rwd = 0
if str(result) == "Result.Victory":
    rwd = 500
else:
    rwd = -500

with open("results.txt","a") as f:
    f.write(f"{result}\n")

map = np.zeros((200, 176, 3), dtype=np.uint8)
observation = map
data = {"state": map, "reward": rwd, "action": None, "terminated": True}  # empty action waiting for the next one!
with open('state_rwd_action.pkl', 'wb') as f:
    pickle.dump(data, f)

cv2.destroyAllWindows()
cv2.waitKey(1)
time.sleep(3)
sys.exit()