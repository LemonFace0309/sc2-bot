from sc2.bot_ai import BotAI  # parent class we inherit from
from sc2.ids.unit_typeid import UnitTypeId
import cv2
import math
import numpy as np

MAX_MINERAL_CONTENT = 1800
SAVE_REPLAY = True

def update_map(self: BotAI):
  map = np.zeros((self.game_info.map_size[0], self.game_info.map_size[1], 3), dtype=np.uint8)

  # draw the minerals:
  for mineral in self.mineral_field:
      pos = mineral.position
      c_visible = [175, 255, 255]
      c_not_visible = [20, 75, 50]
      fraction = mineral.mineral_contents / MAX_MINERAL_CONTENT
      if mineral.is_visible:
          map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction*i) for i in c_visible]
      else:
          map[math.ceil(pos.y)][math.ceil(pos.x)] = c_not_visible 


  # draw the enemy start location:
  for enemy_start_location in self.enemy_start_locations:
      pos = enemy_start_location
      c = [0, 0, 255]
      map[math.ceil(pos.y)][math.ceil(pos.x)] = c

  # draw the enemy units:
  for enemy_unit in self.enemy_units:
      pos = enemy_unit.position
      c = [100, 0, 255]
      # get unit health fraction:
      fraction = enemy_unit.health / enemy_unit.health_max if enemy_unit.health_max > 0 else 0.0001
      map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction*i) for i in c]


  # draw the enemy structures:
  for enemy_structure in self.enemy_structures:
      pos = enemy_structure.position
      c = [0, 100, 255]
      # get structure health fraction:
      fraction = enemy_structure.health / enemy_structure.health_max if enemy_structure.health_max > 0 else 0.0001
      map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction*i) for i in c]

  # draw our structures:
  for our_structure in self.structures:
      if our_structure.type_id == UnitTypeId.NEXUS:
          pos = our_structure.position
          c = [255, 255, 175]
          fraction = our_structure.health / our_structure.health_max if our_structure.health_max > 0 else 0.0001
          map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction*i) for i in c]
      else:
          pos = our_structure.position
          c = [0, 255, 175]
          fraction = our_structure.health / our_structure.health_max if our_structure.health_max > 0 else 0.0001
          map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction*i) for i in c]


  # draw the vespene geysers:
  for vespene in self.vespene_geyser:
      # draw these after buildings, since assimilators go over them. 
      # tried to denote some way that assimilator was on top, couldnt 
      # come up with anything. Tried by positions, but the positions arent identical. ie:
      # vesp position: (50.5, 63.5) 
      # bldg positions: [(64.369873046875, 58.982421875), (52.85693359375, 51.593505859375),...]
      pos = vespene.position
      c_visible = [255, 175, 255]
      c_not_visible = [50,20,75]
      fraction = vespene.vespene_contents / 2250

      if vespene.is_visible:
          map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction*i) for i in c_visible]
      else:
          map[math.ceil(pos.y)][math.ceil(pos.x)] = c_not_visible

  # draw our units:
  for our_unit in self.units:
      # if it is a voidray:
      if our_unit.type_id == UnitTypeId.VOIDRAY:
          pos = our_unit.position
          c = [255, 75 , 75]
          fraction = our_unit.health / our_unit.health_max if our_unit.health_max > 0 else 0.0001
          map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction*i) for i in c]
      else:
          pos = our_unit.position
          c = [175, 255, 0]
          fraction = our_unit.health / our_unit.health_max if our_unit.health_max > 0 else 0.0001
          map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction*i) for i in c]

  # show map with opencv, resized to be larger:
  # horizontal flip:
  cv2.imshow('map',cv2.flip(cv2.resize(map, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST), 0))
  cv2.waitKey(1)

# if SAVE_REPLAY:
#     # save map image into "replays dir"
#     cv2.imwrite(f"replays/serralBot-{int(time.time())}-{iteration}.png", map)

  return map
