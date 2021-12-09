extensions[gis]

breed [vertices vertex]   ;;the nodes
breed [commuters commuter]  ;;people
breed [nodes node]  ;;nodes representing people in networks

globals [
  world-size
  gmu-buildings
  gmu-roads
  gmu-walkway
  gmu-lakes
  gmu-rivers
  gmu-drive
  got_to_destination    ;;count the total number of arrivals
  homes
  works
  hour
  minute
]

patches-own[
  centroid? ;;is it the centroid of a building?
  id   ;;if it is a centroid of a building, it has an ID that represents the building
  entrance ;;nearest vertex on road. only for centroids.
  function ;; 1 for work, 2 for home, 0 for neither
]

commuters-own [
  mynode  ;;a vertex. where he begins his trip
  destination  ;;the destination he wants to arrive at
  destination-entrance  ;;the entrance of the destination on the road
  mypath   ;;an agentset containing nodes to visit in the shortest path
  step-in-path  ;;the number of step taking in the walk
  last-stop ;;last destination
  Myhome  ;;home location
  Mywork  ;;work location
  start_time_h  ;;time to start going to work, hour and minute
  start_time_m
  end_time_h  ;;time to leave work, hour and minute
  end_time_m
  home_friends  ;;list of friends at home
  work_friends ;;list of friends at work
  num_friends  ;;number of friends
  status;; work, home, or transport
  testing  ;;a temp variable used in identifying friends
  happiness_home
  happiness_work
  commuter_id   ;used to link commuters and nodes
]

vertices-own [
  myneighbors  ;;agentset of neighboring vertices
  entrance?  ;;if it is an entrance to a building
  test  ;;used to delete in test

  ;;the follwoing variables are used and renewed in each path-selection
  dist  ;;distance from original point to here
  done ;;1 if has calculated the shortest path through this point, 0 otherwise
  lastnode ;;last node to this point in shortest path
]

nodes-own[
  node_id
]

links-own [
  friend_type
]

to setup
  ca
  reset-ticks

  ;;loading GIS files here
  set gmu-buildings gis:load-dataset "data/Campus_data/Mason_bld.shp"
  set gmu-walkway gis:load-dataset "data/Campus_data/Mason_walkway_line.shp"
  set world-size gis:load-dataset "data/Campus_data/world.shp"
  gis:set-world-envelope gis:envelope-of world-size
  ;;gis:set-world-envelope gis:envelope-of gmu-walkway

  gis:set-drawing-color 5  gis:fill gmu-buildings 1.0

  if show_lakes? [
    set gmu-lakes gis:load-dataset "data/Campus_data/hydrop.shp"
    set gmu-rivers gis:load-dataset "data/Campus_data/hydrol.shp"
    gis:set-drawing-color 87  gis:fill gmu-lakes 1.0
    gis:set-drawing-color 87  gis:draw gmu-rivers 0.5
  ]

  if show_driveway? [
    set gmu-drive gis:load-dataset "data/Campus_data/Mason_Rds.shp"
    gis:set-drawing-color 36  gis:fill gmu-drive 1.0
  ]

  ;gis:set-drawing-color 25  gis:draw gmu-walkway 1.0

  ;identify centroids and assign IDs to centroids
  foreach gis:feature-list-of gmu-buildings [ building ->
    let center-point gis:location-of gis:centroid-of building
    ask patch item 0 center-point item 1 center-point [
      set centroid? true
      set id gis:property-value building "Id"
      set function gis:property-value building "function"
      if function = nobody [set function 0 ]  ;;deal with no data
    ]
  ]

  ;;ask patches with [ centroid? = true][sprout 1 [set size 2 set color red]] ;;use this line to verify

  ;;create turtles representing the nodes. create links to conect them.
  foreach gis:feature-list-of gmu-walkway [ road-feature ->
    foreach gis:vertex-lists-of road-feature [ vertex ->  ; for the road feature, get the list of vertices
      let previous-node-pt nobody
      foreach vertex [ node ->  ; for each vertex in road segment feature
        let location gis:location-of node
        if not empty? location [
          ;ifelse any? vertices with [(xcor = item 0 location and ycor = item 1 location) ] ; if there is not a road-vertex here already
          create-vertices 1 [
            set myneighbors n-of 0 turtles ;;empty
            set xcor item 0 location
            set ycor item 1 location
            set size 0.2
            set shape "circle"
            set color brown
            set hidden? true
            
            ; create link to previous node
            ifelse previous-node-pt = nobody
              [] ; first vertex in feature
              [create-link-with previous-node-pt] ; create link to previous node
            set previous-node-pt self
          ]
        ]
      ]
    ]
  ]

  ;;delete duplicate vertices (there may be more than one vertice on the same patch due to reducing size of the map). therefore, this map is simplified from the original map.
  delete-duplicates

  ;;delete some nodes not connected to the network
  ask vertices [set myneighbors link-neighbors]
  delete-not-connected
  ask vertices [set myneighbors link-neighbors]

  ;;find nearest node to become entrance
  ask patches with [centroid? = true] [
    set entrance min-one-of vertices in-radius 50 [distance myself]
    ask entrance [set entrance? true]
    if show_nodes? [ask vertices [set hidden? false]]
    if show_entrances? [ask entrance [set hidden? false set shape "star" set size 0.5]]
  ]

  set got_to_destination 0

  ;;verification
  ;;ask one-of vertices [set hidden? false set color red ask myneighbors [set hidden? false set color yellow]]

  ask links [set thickness 0.1 set color orange]

  ;;set up homes and work places
  set works patches with [centroid? = true and function = 1]
  set homes patches with [centroid? = true and function = 2]

  create-the-commuters

  set hour 6
  set minute 0

  ;;set up networks
  create-nodes number-of-commuters [set color yellow set node_id who - count commuters
  move-to one-of patches with [pxcor > 45 and count turtles-here < 1 ]]
end

to move
  ;;setting the clock
  set minute minute + 5
  if minute = 60 [
    ifelse hour = 23 [set hour 0] [set hour hour + 1]
    set minute 0
  ]

  ;;checking happiness
  ask commuters with [status = "work"] [
    ifelse (count work_friends > max_friends)
    [
      set happiness_work happiness_work - decrease * (count work_friends - max_friends)
    ]
    [
      ifelse (count work_friends < min_friends)
        [set happiness_work happiness_work - decrease * ( min_friends - count work_friends)]
        [set happiness_work happiness_work + increase]
    ]
    if happiness_work < 0 [relocate_work]
  ]

  ask commuters with [status = "home"] [
    ifelse (count home_friends > max_friends)
    [
      set happiness_home happiness_home - decrease * (count home_friends - max_friends)
    ]
    [
      ifelse (count home_friends < min_friends)
        [set happiness_home happiness_home - decrease * ( min_friends - count home_friends)]
        [set happiness_home happiness_home + increase]
    ]
    if happiness_home < 0 [relocate_home]
  ]

  ;;start going to work
  ask commuters with [status = "home" and hour = start_time_h and minute = start_time_m] [
    set mynode min-one-of vertices [distance myself] move-to mynode ;;move to nearest road
    set destination mywork
    set destination-entrance [entrance] of destination
    ;while [destination-entrance = mynode] [set destination one-of patches with [centroid? = true] set destination-entrance [entrance] of destination]

    ;;select shortest path
    path-select
    set status "transport"
  ]

  ;;start going home
  ask commuters with [status = "work" and hour = end_time_h and minute = end_time_m] [
    set mynode min-one-of vertices [distance myself] move-to mynode ;;move to nearest road
    set destination myhome
    set destination-entrance [entrance] of destination
    ;while [destination-entrance = mynode] [set destination one-of patches with [centroid? = true] set destination-entrance [entrance] of destination]

    ;;select shortest path
    path-select
    set status "transport"
  ]

  ;;move along the path selected
  ask commuters with [status = "transport"] [
    ;ifelse xcor != [xcor] of destination-entrance or ycor != [ycor] of destination-entrance [
    ifelse distance destination-entrance > 0.5
    [
      let next_node item step-in-path mypath
      let dist1 distance next_node
      let remain speed
      while [remain > dist1 and step-in-path < length mypath] [
        move-to next_node
        set step-in-path step-in-path + 1
        set remain remain - dist1
        ifelse step-in-path < length mypath
          [
            set next_node item step-in-path mypath
          ]
          [
            set remain 0
            move-to destination
            if destination = mywork [set status "work"]
            if destination = myhome [set status "home"]
            set got_to_destination got_to_destination + 1
          ]  ;;it has reached destination
        set dist1 distance next_node
      ]
      face next_node fd remain
    ]
    [ ;move-to destination
      move-to destination
      if destination = mywork [set status "work"]
      if destination = myhome [set status "home"]

      set got_to_destination got_to_destination + 1
    ]  ;;arrive and start to work
  ]

  ;;make friends at work. each tick there is a x% chance to make a new friend
  ask commuters with [status = "work"] [
    ask work_friends [set testing 1]
    let non-friends count commuters-here with [testing = 0]  ;;one that is not a friend yet
    if non-friends > 0 and random-float 1 < chance_new_friend [
      let target_friend one-of commuters-here with [testing = 0]

      ask target_friend [
        set work_friends (turtle-set work_friends myself)
      ]
      set work_friends (turtle-set work_friends target_friend )]

    ask work_friends [set testing 0]
  ]

  visualize-networks
  tick
end


;;;;;;;;;;;;;;;;;helper functions;;;;;;;;;;;;;;;;;;;;;;;;;;

to create-the-commuters
  create-commuters number-of-commuters [
    set commuter_id who
    set color white set size 0.5 set shape "person" set destination nobody set last-stop nobody
    ;;set mynode one-of vertices move-to mynode
    set myhome one-of homes set mywork one-of works
    move-to myhome  set status "home"
    set start_time_h round(random-normal 6.5 1)
    ;;will start going to work between 6 and 9
    while [start_time_h < 6 or start_time_h > 9] [
      set start_time_h round(random-normal 6.5 1)
    ]
    set start_time_m (random 12) * 5
    set end_time_h start_time_h + 8  ;will work for 8 hours
    set end_time_m start_time_m
    set happiness_work  100  set happiness_home 100
    set work_friends commuters with [happiness_home < -99999]  ;;empty set
  ]

  ask commuters [set home_friends commuters-here]
end

to delete-duplicates
  ask vertices [
    if count vertices-here > 1 [
      ask other vertices-here [
        ask myself [create-links-with other [link-neighbors] of myself]
        die
      ]
    ]
  ]
end

to delete-not-connected
  ask vertices [set test 0]
  ask one-of vertices [set test 1]
  repeat 500 [
    ask vertices with [test = 1]
    [ask myneighbors [set test 1]]
  ]
  ask vertices with [test = 0][die]
end

to relocate_home
  let old_home myhome
  while [myhome = old_home] [set myhome one-of homes]
  set home_friends commuters with [myhome = [myhome] of myself]
  set happiness_home 100
end

to relocate_work
  let old_work mywork
  while [mywork = old_work] [set mywork one-of works]
  set work_friends commuters with [happiness_work < -99999] ;;empty agent set
  ;;set work_friends nobody
  set happiness_work 100
end

to path-select
  ;;use the A-star algorithm to find the shortest path (shortest in terms of distance)
  set mypath [] set step-in-path 0

  ask vertices [set dist 99999 set done 0 set lastnode nobody set color brown]

  ask mynode [set dist 0] ;;distance to original node is 0

  while [count vertices with [done = 0] > 0] [
    ask vertices with [dist < 99999 and done = 0] [
      ask myneighbors [
        let dist0 distance myself + [dist] of myself    ;;renew the shorstest distance to this point if it is smaller
        if dist > dist0 [
          set dist dist0 set done 0 ;;done=0 if dist renewed, so that it will renew the dist of its neighbors
          set lastnode myself
        ]  ;;record the last node to reach here in the shortest path
        ;set color red  ;;all roads searched will get red
      ]
      set done 1  ;;set done 1 when it has renewed it neighbors
    ]
  ]

  ;print "Found path"

  ;;put nodes in shortest path into a list
  let x destination-entrance

  while [x != mynode] [
    ; if show_path? [ask x [set color yellow] ] ;;highlight the shortest path
    set mypath fput x mypath
    set x [lastnode] of x
  ]
end

to plot_bins_work
  if ticks > 0 [
    clear-plot
    ;set-histogram-num-bars length all_counts
    ask commuters [set num_friends count work_friends]
    histogram [num_friends] of commuters
  ]
end

to plot_bins_home
  if ticks > 0 [
    clear-plot
    ;set-histogram-num-bars length all_counts
    ask commuters [set num_friends count home_friends]
    histogram [num_friends] of commuters
  ]
end

to visualize-networks
  clear-links
  ask commuters with [count work_friends > 0] [
    let friend_nodes nodes with [node_id > 99999] ;;empty set

    ask work_friends with [commuter_id != [commuter_id] of myself][
      let new nodes with [node_id = [commuter_id] of myself]
      set friend_nodes (turtle-set friend_nodes  new)
    ]

    ask nodes with [node_id = [commuter_id] of myself] [
      create-links-with friend_nodes [set color blue]
    ]
  ]

  ask commuters with [count home_friends > 0] [
    let friend_nodes nodes with [node_id > 99999] ;;empty set

    ask home_friends with [commuter_id != [commuter_id] of myself] [
      let new nodes with [node_id = [commuter_id] of myself]
      set friend_nodes (turtle-set friend_nodes  new)
    ]

    ask nodes with [node_id = [commuter_id] of myself] [
      create-links-with friend_nodes  [set color red]
    ]
  ]
end
