def _port_alias_to_name_map_50G(all_ports, s100G_ports):
    new_map = {}
    # 50G ports
    s50G_ports = list(set(all_ports) - set(s100G_ports))

    for i in s50G_ports:
        new_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
        new_map["Ethernet%d/3" % i] = "Ethernet%d" % ((i - 1) * 4 + 2)

    for i in s100G_ports:
        new_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)

    return new_map


def get_port_alias_to_name_map(hostname, hwsku):
    port_alias_to_name_map = {}
    if hwsku == "Force10-S6000":
        for i in range(0, 128, 4):
            port_alias_to_name_map["fortyGigE0/%d" % i] = "Ethernet%d" % i
    elif hwsku == "Force10-S6100":
        for i in range(0, 4):
            for j in range(0, 16):
                port_alias_to_name_map["fortyGigE1/%d/%d" % (i+1, j+1)] = "Ethernet%d" % (i * 16 + j)
    elif hwsku == "Force10-Z9100":
        for i in range(0, 128, 4):
            port_alias_to_name_map["hundredGigE1/%d" % (i/4 + 1)] = "Ethernet%d" % i
    elif hwsku == "Arista-7050-QX32":
        for i in range(1, 25):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
        for i in range(25, 33):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "Arista-7050-QX-32S":
        for i in range(5, 29):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 5) * 4)
        for i in range(29, 37):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % ((i - 5) * 4)
    elif hwsku == "Arista-7260CX3-C64" or hwsku == "Arista-7170-64C":
        for i in range(1, 65):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "Arista-7060CX-32S-C32" or hwsku == "Arista-7060CX-32S-Q32" or hwsku == "Arista-7060CX-32S-C32-T1" or hwsku == "Arista-7170-32CD-C32":
        for i in range(1, 33):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "Mellanox-SN2700-D48C8":
        # 50G ports
        s50G_ports = [x for x in range(0, 24, 2)] + [x for x in range(40, 88, 2)] + [x for x in range(104, 128, 2)]

        # 100G ports
        s100G_ports = [x for x in range(24, 40, 4)] + [x for x in range(88, 104, 4)]

        for i in s50G_ports:
            alias = "etp%d" % (i / 4 + 1) + ("a" if i % 4 == 0 else "b")
            port_alias_to_name_map[alias] = "Ethernet%d" % i
        for i in s100G_ports:
            alias = "etp%d" % (i / 4 + 1)
            port_alias_to_name_map[alias] = "Ethernet%d" % i
    elif (hwsku == "Mellanox-SN2700" or hwsku == "ACS-MSN2700") or \
         (hwsku == "ACS-MSN3700") or (hwsku == "ACS-MSN3700C") or \
         (hwsku == "ACS-MSN3800") or (hwsku == "Mellanox-SN3800-D112C8") or \
         (hwsku == "ACS-MSN4700") or (hwsku == "ACS-MSN4600C") or \
         (hwsku == "ACS-MSN3420"):
        if hostname == "arc-switch1038":
            for i in range(1, 17):
                port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1) * 4)

            port_alias_to_name_map["etp17a"] = "Ethernet64"
            port_alias_to_name_map["etp17b"] = "Ethernet65"
            port_alias_to_name_map["etp17c"] = "Ethernet66"
            port_alias_to_name_map["etp17d"] = "Ethernet67"
            port_alias_to_name_map["etp21a"] = "Ethernet80"
            port_alias_to_name_map["etp21b"] = "Ethernet82"

            for i in range(23, 33):
                port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1) * 4)
        elif hostname == "r-tigris-04":
            port_alias_to_name_map["etp1a"] = "Ethernet0"
            port_alias_to_name_map["etp1b"] = "Ethernet2"
            port_alias_to_name_map["etp2a"] = "Ethernet4"
            port_alias_to_name_map["etp2b"] = "Ethernet6"
            port_alias_to_name_map["etp3a"] = "Ethernet8"
            port_alias_to_name_map["etp3b"] = "Ethernet10"
            port_alias_to_name_map["etp4a"] = "Ethernet12"
            port_alias_to_name_map["etp4b"] = "Ethernet14"
            port_alias_to_name_map["etp5a"] = "Ethernet16"
            port_alias_to_name_map["etp5b"] = "Ethernet18"
            port_alias_to_name_map["etp6a"] = "Ethernet20"
            port_alias_to_name_map["etp6b"] = "Ethernet22"
            port_alias_to_name_map["etp7a"] = "Ethernet24"
            port_alias_to_name_map["etp7b"] = "Ethernet26"
            port_alias_to_name_map["etp8a"] = "Ethernet28"
            port_alias_to_name_map["etp8b"] = "Ethernet30"
            port_alias_to_name_map["etp9a"] = "Ethernet32"
            port_alias_to_name_map["etp9b"] = "Ethernet34"
            port_alias_to_name_map["etp10a"] = "Ethernet36"
            port_alias_to_name_map["etp10b"] = "Ethernet38"
            port_alias_to_name_map["etp11a"] = "Ethernet40"
            port_alias_to_name_map["etp11b"] = "Ethernet42"
            port_alias_to_name_map["etp12a"] = "Ethernet44"
            port_alias_to_name_map["etp12b"] = "Ethernet46"
            port_alias_to_name_map["etp13a"] = "Ethernet48"
            port_alias_to_name_map["etp13b"] = "Ethernet50"
            port_alias_to_name_map["etp14a"] = "Ethernet52"
            port_alias_to_name_map["etp14b"] = "Ethernet54"
            port_alias_to_name_map["etp15a"] = "Ethernet56"
            port_alias_to_name_map["etp15b"] = "Ethernet58"
            port_alias_to_name_map["etp16a"] = "Ethernet60"
            port_alias_to_name_map["etp16b"] = "Ethernet62"
            port_alias_to_name_map["etp17a"] = "Ethernet64"
            port_alias_to_name_map["etp17b"] = "Ethernet66"
            port_alias_to_name_map["etp18a"] = "Ethernet68"
            port_alias_to_name_map["etp18b"] = "Ethernet70"
            port_alias_to_name_map["etp19a"] = "Ethernet72"
            port_alias_to_name_map["etp19b"] = "Ethernet74"
            port_alias_to_name_map["etp20a"] = "Ethernet76"
            port_alias_to_name_map["etp20b"] = "Ethernet78"
            port_alias_to_name_map["etp21a"] = "Ethernet80"
            port_alias_to_name_map["etp21b"] = "Ethernet82"
            port_alias_to_name_map["etp22a"] = "Ethernet84"
            port_alias_to_name_map["etp22b"] = "Ethernet86"
            port_alias_to_name_map["etp23a"] = "Ethernet88"
            port_alias_to_name_map["etp23b"] = "Ethernet90"
            port_alias_to_name_map["etp24a"] = "Ethernet92"
            port_alias_to_name_map["etp24b"] = "Ethernet94"
            port_alias_to_name_map["etp25"] = "Ethernet96"
            port_alias_to_name_map["etp26"] = "Ethernet100"
            port_alias_to_name_map["etp27a"] = "Ethernet104"
            port_alias_to_name_map["etp27b"] = "Ethernet106"
            port_alias_to_name_map["etp28a"] = "Ethernet108"
            port_alias_to_name_map["etp28b"] = "Ethernet110"
            port_alias_to_name_map["etp29"] = "Ethernet112"
            port_alias_to_name_map["etp30"] = "Ethernet116"
            port_alias_to_name_map["etp31a"] = "Ethernet120"
            port_alias_to_name_map["etp31b"] = "Ethernet122"
            port_alias_to_name_map["etp32a"] = "Ethernet124"
            port_alias_to_name_map["etp32b"] = "Ethernet126"
            port_alias_to_name_map["etp33"] = "Ethernet128"
            port_alias_to_name_map["etp34"] = "Ethernet132"
            port_alias_to_name_map["etp35a"] = "Ethernet136"
            port_alias_to_name_map["etp35b"] = "Ethernet138"
            port_alias_to_name_map["etp36a"] = "Ethernet140"
            port_alias_to_name_map["etp36b"] = "Ethernet142"
            port_alias_to_name_map["etp37"] = "Ethernet144"
            port_alias_to_name_map["etp38"] = "Ethernet148"
            port_alias_to_name_map["etp39a"] = "Ethernet152"
            port_alias_to_name_map["etp39b"] = "Ethernet154"
            port_alias_to_name_map["etp40a"] = "Ethernet156"
            port_alias_to_name_map["etp40b"] = "Ethernet158"
            port_alias_to_name_map["etp41a"] = "Ethernet160"
            port_alias_to_name_map["etp41b"] = "Ethernet162"
            port_alias_to_name_map["etp42a"] = "Ethernet164"
            port_alias_to_name_map["etp42b"] = "Ethernet166"
            port_alias_to_name_map["etp43a"] = "Ethernet168"
            port_alias_to_name_map["etp43b"] = "Ethernet170"
            port_alias_to_name_map["etp44a"] = "Ethernet172"
            port_alias_to_name_map["etp44b"] = "Ethernet174"
            port_alias_to_name_map["etp45a"] = "Ethernet176"
            port_alias_to_name_map["etp45b"] = "Ethernet178"
            port_alias_to_name_map["etp46a"] = "Ethernet180"
            port_alias_to_name_map["etp46b"] = "Ethernet182"
            port_alias_to_name_map["etp47a"] = "Ethernet184"
            port_alias_to_name_map["etp47b"] = "Ethernet186"
            port_alias_to_name_map["etp48a"] = "Ethernet188"
            port_alias_to_name_map["etp48b"] = "Ethernet190"
            port_alias_to_name_map["etp49a"] = "Ethernet192"
            port_alias_to_name_map["etp49b"] = "Ethernet194"
            port_alias_to_name_map["etp50a"] = "Ethernet196"
            port_alias_to_name_map["etp50b"] = "Ethernet198"
            port_alias_to_name_map["etp51a"] = "Ethernet200"
            port_alias_to_name_map["etp51b"] = "Ethernet202"
            port_alias_to_name_map["etp52a"] = "Ethernet204"
            port_alias_to_name_map["etp52b"] = "Ethernet206"
            port_alias_to_name_map["etp53a"] = "Ethernet208"
            port_alias_to_name_map["etp53b"] = "Ethernet210"
            port_alias_to_name_map["etp54a"] = "Ethernet212"
            port_alias_to_name_map["etp54b"] = "Ethernet214"
            port_alias_to_name_map["etp55a"] = "Ethernet216"
            port_alias_to_name_map["etp55b"] = "Ethernet218"
            port_alias_to_name_map["etp56a"] = "Ethernet220"
            port_alias_to_name_map["etp56b"] = "Ethernet222"
            port_alias_to_name_map["etp57a"] = "Ethernet224"
            port_alias_to_name_map["etp57b"] = "Ethernet226"
            port_alias_to_name_map["etp58a"] = "Ethernet228"
            port_alias_to_name_map["etp58b"] = "Ethernet230"
            port_alias_to_name_map["etp59a"] = "Ethernet232"
            port_alias_to_name_map["etp59b"] = "Ethernet234"
            port_alias_to_name_map["etp60a"] = "Ethernet236"
            port_alias_to_name_map["etp60b"] = "Ethernet238"
            port_alias_to_name_map["etp61a"] = "Ethernet240"
            port_alias_to_name_map["etp61b"] = "Ethernet242"
            port_alias_to_name_map["etp62a"] = "Ethernet244"
            port_alias_to_name_map["etp62b"] = "Ethernet246"
            port_alias_to_name_map["etp63a"] = "Ethernet248"
            port_alias_to_name_map["etp63b"] = "Ethernet250"
            port_alias_to_name_map["etp64a"] = "Ethernet252"
            port_alias_to_name_map["etp64b"] = "Ethernet254"
        elif hostname == "r-tigon-04":
            port_alias_to_name_map["etp1a"] = "Ethernet0"
            port_alias_to_name_map["etp1b"] = "Ethernet2"
            port_alias_to_name_map["etp2a"] = "Ethernet8"
            port_alias_to_name_map["etp2b"] = "Ethernet10"
            port_alias_to_name_map["etp3a"] = "Ethernet16"
            port_alias_to_name_map["etp3b"] = "Ethernet18"
            port_alias_to_name_map["etp4"] = "Ethernet24"
            port_alias_to_name_map["etp5a"] = "Ethernet32"
            port_alias_to_name_map["etp5b"] = "Ethernet34"
            port_alias_to_name_map["etp6a"] = "Ethernet40"
            port_alias_to_name_map["etp6b"] = "Ethernet42"
            port_alias_to_name_map["etp7a"] = "Ethernet48"
            port_alias_to_name_map["etp7b"] = "Ethernet50"
            port_alias_to_name_map["etp8"] = "Ethernet56"
            port_alias_to_name_map["etp9a"] = "Ethernet64"
            port_alias_to_name_map["etp9b"] = "Ethernet66"
            port_alias_to_name_map["etp10a"] = "Ethernet72"
            port_alias_to_name_map["etp10b"] = "Ethernet74"
            port_alias_to_name_map["etp11a"] = "Ethernet80"
            port_alias_to_name_map["etp11b"] = "Ethernet82"
            port_alias_to_name_map["etp12"] = "Ethernet88"
            port_alias_to_name_map["etp13a"] = "Ethernet96"
            port_alias_to_name_map["etp13b"] = "Ethernet98"
            port_alias_to_name_map["etp14a"] = "Ethernet104"
            port_alias_to_name_map["etp14b"] = "Ethernet106"
            port_alias_to_name_map["etp15a"] = "Ethernet112"
            port_alias_to_name_map["etp15b"] = "Ethernet114"
            port_alias_to_name_map["etp16"] = "Ethernet120"
            port_alias_to_name_map["etp17a"] = "Ethernet128"
            port_alias_to_name_map["etp17b"] = "Ethernet130"
            port_alias_to_name_map["etp18a"] = "Ethernet136"
            port_alias_to_name_map["etp18b"] = "Ethernet138"
            port_alias_to_name_map["etp19a"] = "Ethernet144"
            port_alias_to_name_map["etp19b"] = "Ethernet146"
            port_alias_to_name_map["etp20"] = "Ethernet152"
            port_alias_to_name_map["etp21a"] = "Ethernet160"
            port_alias_to_name_map["etp21b"] = "Ethernet162"
            port_alias_to_name_map["etp22a"] = "Ethernet168"
            port_alias_to_name_map["etp22b"] = "Ethernet170"
            port_alias_to_name_map["etp23a"] = "Ethernet176"
            port_alias_to_name_map["etp23b"] = "Ethernet178"
            port_alias_to_name_map["etp24"] = "Ethernet184"
            port_alias_to_name_map["etp25"] = "Ethernet192"
            port_alias_to_name_map["etp26"] = "Ethernet200"
            port_alias_to_name_map["etp27a"] = "Ethernet208"
            port_alias_to_name_map["etp27b"] = "Ethernet210"
            port_alias_to_name_map["etp28"] = "Ethernet216"
            port_alias_to_name_map["etp29"] = "Ethernet224"
            port_alias_to_name_map["etp30"] = "Ethernet232"
            port_alias_to_name_map["etp31a"] = "Ethernet240"
            port_alias_to_name_map["etp31b"] = "Ethernet242"
            port_alias_to_name_map["etp32"] = "Ethernet248"
            port_alias_to_name_map["etp33"] = "Ethernet256"
            port_alias_to_name_map["etp34"] = "Ethernet264"
            port_alias_to_name_map["etp35a"] = "Ethernet272"
            port_alias_to_name_map["etp35b"] = "Ethernet274"
            port_alias_to_name_map["etp36"] = "Ethernet280"
            port_alias_to_name_map["etp37"] = "Ethernet288"
            port_alias_to_name_map["etp38"] = "Ethernet296"
            port_alias_to_name_map["etp39a"] = "Ethernet304"
            port_alias_to_name_map["etp39b"] = "Ethernet306"
            port_alias_to_name_map["etp40"] = "Ethernet312"
            port_alias_to_name_map["etp41a"] = "Ethernet320"
            port_alias_to_name_map["etp41b"] = "Ethernet322"
            port_alias_to_name_map["etp42a"] = "Ethernet328"
            port_alias_to_name_map["etp42b"] = "Ethernet330"
            port_alias_to_name_map["etp43a"] = "Ethernet336"
            port_alias_to_name_map["etp43b"] = "Ethernet338"
            port_alias_to_name_map["etp44"] = "Ethernet344"
            port_alias_to_name_map["etp45a"] = "Ethernet352"
            port_alias_to_name_map["etp45b"] = "Ethernet354"
            port_alias_to_name_map["etp46a"] = "Ethernet360"
            port_alias_to_name_map["etp46b"] = "Ethernet362"
            port_alias_to_name_map["etp47a"] = "Ethernet368"
            port_alias_to_name_map["etp47b"] = "Ethernet370"
            port_alias_to_name_map["etp48"] = "Ethernet376"
            port_alias_to_name_map["etp49a"] = "Ethernet384"
            port_alias_to_name_map["etp49b"] = "Ethernet386"
            port_alias_to_name_map["etp50a"] = "Ethernet392"
            port_alias_to_name_map["etp50b"] = "Ethernet394"
            port_alias_to_name_map["etp51a"] = "Ethernet400"
            port_alias_to_name_map["etp51b"] = "Ethernet402"
            port_alias_to_name_map["etp52"] = "Ethernet408"
            port_alias_to_name_map["etp53a"] = "Ethernet416"
            port_alias_to_name_map["etp53b"] = "Ethernet418"
            port_alias_to_name_map["etp54a"] = "Ethernet424"
            port_alias_to_name_map["etp54b"] = "Ethernet426"
            port_alias_to_name_map["etp55a"] = "Ethernet432"
            port_alias_to_name_map["etp55b"] = "Ethernet434"
            port_alias_to_name_map["etp56"] = "Ethernet440"
            port_alias_to_name_map["etp57a"] = "Ethernet448"
            port_alias_to_name_map["etp57b"] = "Ethernet450"
            port_alias_to_name_map["etp58a"] = "Ethernet456"
            port_alias_to_name_map["etp58b"] = "Ethernet458"
            port_alias_to_name_map["etp59a"] = "Ethernet464"
            port_alias_to_name_map["etp59b"] = "Ethernet466"
            port_alias_to_name_map["etp60"] = "Ethernet472"
            port_alias_to_name_map["etp61a"] = "Ethernet480"
            port_alias_to_name_map["etp61b"] = "Ethernet482"
            port_alias_to_name_map["etp62a"] = "Ethernet488"
            port_alias_to_name_map["etp62b"] = "Ethernet490"
            port_alias_to_name_map["etp63"] = "Ethernet496"
            port_alias_to_name_map["etp64"] = "Ethernet504"
        elif hostname == "r-tigris-13":
            for i in range(1, 65):
                port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1) * 4)
        elif hostname == "r-leopard-01":
            for i in range(1, 33):
                port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1) * 8)
        else:
            for i in range(1, 33):
                port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "Arista-7060CX-32S-D48C8":
        # All possible breakout 50G port numbers:
        all_ports = [ x for x in range(1, 33)]

        # 100G ports
        s100G_ports = [ x for x in range(7, 11) ]
        s100G_ports += [ x for x in range(23, 27) ]

        port_alias_to_name_map = port_alias_to_name_map_50G(all_ports, s100G_ports)
    elif hwsku == "Arista-7260CX3-D108C8":
        # All possible breakout 50G port numbers:
        all_ports = [ x for x in range(1, 65)]

        # 100G ports
        s100G_ports = [ x for x in range(13, 21) ]

        port_alias_to_name_map = port_alias_to_name_map_50G(all_ports, s100G_ports)
    elif hwsku == "INGRASYS-S9100-C32":
        for i in range(1, 33):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "INGRASYS-S9100-C32" or hwsku == "INGRASYS-S9130-32X" or hwsku == "INGRASYS-S8810-32Q":
        for i in range(1, 33):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "INGRASYS-S8900-54XC":
        for i in range(1, 49):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % (i - 1)
        for i in range(49, 55):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 49) * 4 + 48)
    elif hwsku == "INGRASYS-S8900-64XC":
        for i in range(1, 49):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % (i - 1)
        for i in range(49, 65):
            port_alias_to_name_map["Ethernet%d/1" % i] = "Ethernet%d" % ((i - 49) * 4 + 48)
    elif hwsku == "Accton-AS7712-32X":
        for i in range(1, 33):
            port_alias_to_name_map["hundredGigE%d" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "Celestica-DX010-C32":
        for i in range(1, 33):
            port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "Seastone-DX010":
        for i in range(1, 33):
            port_alias_to_name_map["Eth%d" % i] = "Ethernet%d" % ((i - 1) * 4)
    elif hwsku == "Celestica-E1031-T48S4":
        for i in range(1, 53):
            port_alias_to_name_map["etp%d" % i] = "Ethernet%d" % ((i - 1))
    elif hwsku == "et6448m":
        for i in range(0, 52):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % i
    elif hwsku == "newport":
        for i in range(0, 256, 8):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % i
    else:
        for i in range(0, 128, 4):
            port_alias_to_name_map["Ethernet%d" % i] = "Ethernet%d" % i

    return port_alias_to_name_map

