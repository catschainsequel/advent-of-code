import itertools


def try_steps(steps, xrange=range(-50, 50+1), yrange=range(-50, 50+1), zrange=range(-50, 50+1)):
    reactor = [[[False for x in xrange]
                for y in yrange]
               for z in zrange]

    for (x_start, x_end, y_start, y_end, z_start, z_end, new_state) in steps:
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end + 1):
                for z in range(z_start, z_end + 1):
                    reactor[x][y][z] = new_state

    c = 0
    for x, y, z in itertools.product(xrange,
                                     yrange,
                                     zrange):
        if reactor[x][y][z]:
            c += 1
    print(c)


def try_steps_v2(steps, xrange=range(-50, 50+1), yrange=range(-50, 50+1), zrange=range(-50, 50+1)):
    c = 0
    for x, y, z in itertools.product(xrange, yrange, zrange):
        if x % 1000 == 0:
            print("Current x: %s" % x)
        on = False
        for (x_start, x_end, y_start, y_end, z_start, z_end, new_state) in steps:
            if (x_start <= x and x <= x_end and
                y_start <= y and y <= y_end and
                    z_start <= z and z <= z_end):
                on = new_state
        if on:
            c += 1
    print(c)


class Region():
    def __init__(self, x_start, x_end, y_start, y_end, z_start, z_end, subregions):
        self.x_start = x_start
        self.x_end = x_end
        self.y_start = y_start
        self.y_end = y_end
        self.z_start = z_start
        self.z_end = z_end
        self.subregions = subregions


class RegionV2():
    def __init__(self, x_start, x_end, y_start, y_end, z_start, z_end, is_on):
        self.x_start = x_start
        self.x_end = x_end
        self.y_start = y_start
        self.y_end = y_end
        self.z_start = z_start
        self.z_end = z_end
        self.is_on = is_on

    def __str__(self):
        return "(%s, %s) x (%s, %s) x (%s, %s) %s" % (self.x_start, self.x_end, self.y_start, self.y_end, self.z_start, self.z_end, self.is_on)
    
    def __hash__(self) -> int:
        return hash((self.x_start, self.x_end, self.y_start, self.y_end, self.z_start, self.z_end, self.is_on))
    
    def __eq__(self, other):
        return (self.x_start == other.x_start
                and self.x_end == other.x_end
                and self.y_start == other.y_start
                and self.y_end == other.y_end
                and self.z_start == other.z_start
                and self.z_end == other.z_end
                and self.is_on == other.is_on)

    @classmethod
    def make(cls, xr, yr, zr, is_on):
        return RegionV2(xr[0], xr[1], yr[0], yr[1], zr[0], zr[1], is_on)


def overlaps(region1, region2):
    # Returns true if 2 regions overlap
    return ((region2.x_start <= region1.x_end and region2.x_end >= region1.x_start)
            and (region2.y_start <= region1.y_end and region2.y_end >= region1.y_start)
            and (region2.z_start <= region1.z_end and region2.z_end >= region1.z_start))


def combine_regions(regions_to_merge):
    x_start = min([region.x_start for region in regions_to_merge])
    x_end = max([region.x_end for region in regions_to_merge])
    y_start = min([region.y_start for region in regions_to_merge])
    y_end = max([region.y_end for region in regions_to_merge])
    z_start = min([region.z_start for region in regions_to_merge])
    z_end = max([region.z_end for region in regions_to_merge])
    subregions = [
        subregion for region in regions_to_merge for subregion in region.subregions]
    return Region(x_start, x_end, y_start, y_end, z_start, z_end, subregions)


def separate_into_new_ranges(existing_start, existing_end, new_start, new_end):
    existing_ranges = []
    new_ranges = []
    overlapping_ranges = []
    if new_start < existing_start:
        new_ranges.append((new_start, existing_start - 1))
        if new_end < existing_end:
            overlapping_ranges.append((existing_start, new_end))
            existing_ranges.append((new_end + 1, existing_end))
        elif new_end == existing_end:
            overlapping_ranges.append((existing_start, new_end))
        elif new_end > existing_end:
            overlapping_ranges.append((existing_start, existing_end))
            new_ranges.append((existing_end + 1, new_end))
    elif new_start == existing_start:
        if new_end < existing_end:
            overlapping_ranges.append((existing_start, new_end))
            existing_ranges.append((new_end + 1, existing_end))
        elif new_end == existing_end:
            overlapping_ranges.append((existing_start, new_end))
        elif new_end > existing_end:
            overlapping_ranges.append((existing_start, existing_end))
            new_ranges.append((existing_end + 1, new_end))
    elif new_start > existing_start:
        existing_ranges.append((existing_start, new_start - 1))
        if new_end < existing_end:
            overlapping_ranges.append((new_start, new_end))
            existing_ranges.append((new_end + 1, existing_end))
        elif new_end == existing_end:
            overlapping_ranges.append((new_start, new_end))
        elif new_end > existing_end:
            overlapping_ranges.append((new_start, existing_end))
            new_ranges.append((existing_end + 1, new_end))
    return (existing_ranges, new_ranges, overlapping_ranges)


def simplify_ranges(ranges):
    # sort ranges
    ranges.sort(key=lambda x: x[0])

    # if ranges are adjacent, combine
    new_ranges = [ranges[0]]
    for range in ranges[1:]:
        if new_ranges[-1][1] + 1 >= range[0]:
            new_ranges[-1] = (new_ranges[-1][0], range[1])
        else:
            new_ranges.append(range)

    # eliminate dupes
    return [new_range for new_range in new_ranges if new_range[0] != new_range[1]]


def apply_new_region(existing_regions, region_to_add):
    # Returns a new list of non-overlapping regions.
    new_regions = [region_to_add]
    rechopped_older_regions = []
    for existing_region in existing_regions:
        final_new_regions = []
        # print("Starting new regions: %s" % "\n".join(str(nr) for nr in new_regions))
        for new_region in new_regions:
            # Slice every new_region in new_regions across all areas of overlap.
            # Eliminate 0-sized regions
            (existing_x_ranges, new_x_ranges, overlapping_x_ranges) = separate_into_new_ranges(
                existing_region.x_start, existing_region.x_end, region_to_add.x_start, region_to_add.x_end)
            (existing_y_ranges, new_y_ranges, overlapping_y_ranges) = separate_into_new_ranges(
                existing_region.y_start, existing_region.y_end, region_to_add.y_start, region_to_add.y_end)
            (existing_z_ranges, new_z_ranges, overlapping_z_ranges) = separate_into_new_ranges(
                existing_region.z_start, existing_region.z_end, region_to_add.z_start, region_to_add.z_end)

            # All overlapping = overlap.
            # Combines existing and new = not a region.
            # Only new or only existing with some overlap = new or existing
            if region_to_add.is_on:
                rechopped_older_regions.extend([RegionV2.make(xr, yr, zr, region_to_add.is_on)
                                                for xr, yr, zr in itertools.product(overlapping_x_ranges,
                                                                                    overlapping_y_ranges,
                                                                                    overlapping_z_ranges)
                                                if xr[1] >= xr[0] and yr[1] >= yr[0] and zr[1] >= zr[0]])

            if existing_region.is_on:
                rechopped_older_regions.extend([RegionV2.make(xr, yr, zr, existing_region.is_on)
                                                for xr, yr, zr in itertools.chain(itertools.product(existing_x_ranges, existing_y_ranges, existing_z_ranges)
                                                , itertools.product(existing_x_ranges, existing_y_ranges, overlapping_z_ranges)
                                                , itertools.product(existing_x_ranges, overlapping_y_ranges, existing_z_ranges)
                                                , itertools.product(overlapping_x_ranges, existing_y_ranges, existing_z_ranges)
                                                , itertools.product(existing_x_ranges, overlapping_y_ranges, overlapping_z_ranges)
                                                , itertools.product(overlapping_x_ranges, overlapping_y_ranges, existing_z_ranges)
                                                , itertools.product(overlapping_x_ranges, existing_y_ranges, overlapping_z_ranges))
                                                if xr[1] >= xr[0] and yr[1] >= yr[0] and zr[1] >= zr[0]])
            if region_to_add.is_on:
                final_new_regions.extend([RegionV2.make(xr, yr, zr, region_to_add.is_on)
                                                for xr, yr, zr in itertools.chain(itertools.product(new_x_ranges, new_y_ranges, new_z_ranges)
                                                , itertools.product(new_x_ranges, new_y_ranges, overlapping_z_ranges)
                                                , itertools.product(new_x_ranges, overlapping_y_ranges, new_z_ranges)
                                                , itertools.product(overlapping_x_ranges, new_y_ranges, new_z_ranges)
                                                , itertools.product(new_x_ranges, overlapping_y_ranges, overlapping_z_ranges)
                                                , itertools.product(overlapping_x_ranges, overlapping_y_ranges, new_z_ranges)
                                                , itertools.product(overlapping_x_ranges, new_y_ranges, overlapping_z_ranges))
                                                if xr[1] >= xr[0] and yr[1] >= yr[0] and zr[1] >= zr[0]])
        new_regions = list(set(final_new_regions))
        # print("Ending new regions: %s" % "\n".join(str(nr) for nr in new_regions))

    return (new_regions, rechopped_older_regions)


def get_on_cubes(region):
    return try_steps_v2(region.subregions,
                        range(region.x_start, region.x_end+1),
                        range(region.y_start, region.y_end+1),
                        range(region.z_start, region.z_end+1))


def get_on_cubes_v2(region):
    if region.is_on:
        return ((region.x_end + 1 - region.x_start)
                * (region.y_end + 1 - region.y_start)
                * (region.z_end + 1 - region.z_start))


def find_cube_on_count(input_regions):
    print("Starting with %s unmerged regions" % len(input_regions))

    # Add seed region
    nonoverlapping_regions = [input_regions[0]]
    print("First region: %s" % input_regions[0])

    for region_to_merge in input_regions[1:]:
        print("Merging in region: %s" % region_to_merge)
        regions_to_recalculate_idx = [pos
                                      for pos, region in enumerate(nonoverlapping_regions)
                                      if overlaps(region, region_to_merge)]
        print("Need to recalculate %s of %s existing regions" % (len(regions_to_recalculate_idx), len(nonoverlapping_regions)))
        regions_to_recalculate = [nonoverlapping_regions[i]
                                  for i in regions_to_recalculate_idx]
        for index in sorted(regions_to_recalculate_idx, reverse=True):
            del nonoverlapping_regions[index]

        (new_regions, rechopped_older_regions) = apply_new_region(
            regions_to_recalculate, region_to_merge)

        # print("New regions: \n %s" % "\n".join(str(region)
        #       for region in new_regions))
        # print("Rechopped older regions: \n %s" % "\n".join(str(region)
        #       for region in rechopped_older_regions))
        nonoverlapping_regions.extend(new_regions)
        nonoverlapping_regions.extend(rechopped_older_regions)
        print("Compressing existing %s regions" % len(nonoverlapping_regions))
        nonoverlapping_regions = list(set(nonoverlapping_regions))
        print("%s regions after compression" % len(nonoverlapping_regions))

    print("%s distinct regions found" % len(nonoverlapping_regions))
    # nonoverlapping_regions.sort(lambda region: (region.x_start, region.y_start, region.z_start))
    print(sum([get_on_cubes_v2(region) for region in nonoverlapping_regions]))


def parseline(line):
    on_off, coords = line.split(" ")
    x, y, z = coords.split(",")
    [x_start, x_end] = [int(i) for i in x.split("=")[1].split("..")]
    [y_start, y_end] = [int(i) for i in y.split("=")[1].split("..")]
    [z_start, z_end] = [int(i) for i in z.split("=")[1].split("..")]
    return RegionV2(x_start, x_end, y_start, y_end, z_start, z_end, on_off == "on")

input = [parseline(line) for line in """on x=-45..0,y=-44..9,z=-39..10
on x=-22..26,y=-21..25,z=-2..43
on x=-17..35,y=-35..15,z=-27..25
on x=-10..38,y=-46..6,z=-19..31
on x=-19..28,y=-48..4,z=-47..4
on x=-12..41,y=-45..7,z=-47..1
on x=-31..15,y=-49..-1,z=-18..30
on x=-15..32,y=-36..12,z=-12..33
on x=-47..2,y=-35..12,z=-9..37
on x=-8..39,y=-41..10,z=-1..45
off x=26..43,y=-37..-18,z=28..37
on x=-12..34,y=-29..22,z=-17..35
off x=-14..-5,y=27..39,z=8..19
on x=-29..25,y=-36..9,z=-7..37
off x=-5..13,y=27..41,z=-2..13
on x=-3..47,y=-33..16,z=-29..20
off x=33..46,y=-26..-13,z=-21..-3
on x=-36..16,y=-33..17,z=-7..42
off x=-20..-10,y=-25..-10,z=-11..6
on x=-32..17,y=-2..42,z=-5..41
on x=-14096..20560,y=68592..91734,z=-24114..-3064
on x=12963..22528,y=55868..77961,z=-58899..-29368
on x=-47265..-37348,y=18605..46523,z=46563..81594
on x=-59154..-48032,y=-48920..-34924,z=-60525..-32819
on x=-5530..16500,y=-15425..7600,z=-94763..-66170
on x=-36660..-24876,y=-1308..16629,z=66030..88806
on x=46439..80056,y=26862..48487,z=29564..55890
on x=69990..95984,y=-19445..-3308,z=-3203..21710
on x=35623..64389,y=-15763..4727,z=-71119..-41215
on x=-5497..21415,y=-86066..-69027,z=22220..36576
on x=-38552..-19939,y=-48049..-14214,z=53056..79609
on x=4665..28252,y=19548..47796,z=-91960..-67778
on x=-68878..-44092,y=-62121..-40771,z=13161..45585
on x=-2131..15836,y=-3579..15491,z=70830..95182
on x=2593..13937,y=61992..90081,z=15739..45257
on x=-78668..-52364,y=26650..32845,z=20572..38558
on x=-44752..-20387,y=44765..72700,z=28888..51911
on x=-29533..-8399,y=58637..86541,z=-26487..-12007
on x=1296..33512,y=9843..36959,z=72351..90372
on x=29955..48144,y=-79033..-58067,z=-43517..-11838
on x=-12785..11365,y=26778..45792,z=-79483..-56479
on x=50177..55401,y=-60805..-38482,z=-41568..-30885
on x=25332..64698,y=30367..58667,z=39206..57677
on x=50992..67686,y=21323..34514,z=-61675..-47321
on x=-16067..11414,y=-75769..-41109,z=36003..73850
on x=63830..75313,y=-47416..-20715,z=-24897..-8896
on x=6288..34739,y=-92258..-58206,z=-24675..-4289
on x=56795..93515,y=11226..27023,z=-39696..-12254
on x=-74394..-38807,y=35319..63061,z=26868..47975
on x=-33625..-17148,y=-83804..-60871,z=-12498..-303
on x=59431..69218,y=-10897..7070,z=-70023..-50511
on x=27683..34278,y=-58688..-49729,z=-49218..-34608
on x=-68157..-42582,y=53016..72391,z=-29399..2159
on x=37673..73185,y=38813..60864,z=15102..45372
on x=-57169..-35158,y=-37421..-11638,z=45932..71249
on x=48238..62384,y=8236..32521,z=40094..68699
on x=-34881..-20180,y=73385..74490,z=1989..8473
on x=14650..43394,y=15317..32207,z=-86924..-55784
on x=54034..77112,y=40402..53516,z=-31575..-18574
on x=-3676..3515,y=41046..61651,z=39802..59299
on x=-62141..-50216,y=49149..50884,z=-32595..-5875
on x=-63580..-35658,y=21993..36827,z=-59990..-45594
on x=75192..91990,y=-32329..-15336,z=10007..29003
on x=22149..45279,y=-39068..-30086,z=-73245..-53076
on x=63783..79729,y=-19100..1185,z=7884..26618
on x=-44475..-18461,y=4942..16258,z=-75090..-58262
on x=52461..69373,y=52299..56788,z=-18656..3104
on x=4548..36708,y=46879..55923,z=40062..72572
on x=-90197..-70261,y=-31557..-7445,z=4591..12754
on x=-15919..-8050,y=-28053..-4561,z=-78594..-57971
on x=-734..7161,y=-92174..-76838,z=-22320..-16446
on x=-1857..29127,y=-89402..-73684,z=-39071..-6833
on x=3390..26338,y=2369..14518,z=-85146..-75744
on x=1640..24013,y=14782..39665,z=61448..91383
on x=-23732..-1839,y=66610..68137,z=31644..61985
on x=51026..79780,y=-9260..6938,z=46650..59398
on x=-31561..-23350,y=-79629..-55721,z=-51901..-23077
on x=-27031..-9516,y=43327..63105,z=-63597..-46263
on x=17062..30469,y=-9201..11425,z=-78860..-76297
on x=57076..81867,y=-38467..-21153,z=7683..35867
on x=33022..40737,y=34019..48626,z=53864..56420
on x=2937..18415,y=11640..30242,z=77532..96256
on x=43636..72834,y=37690..64241,z=-15938..-2188
on x=-39533..-21683,y=-59492..-55763,z=-62498..-25776
on x=48040..62315,y=-21569..-7226,z=-69716..-42699
on x=7784..38508,y=36944..50705,z=-76106..-57577
on x=-17845..-1108,y=-38150..-24088,z=67805..89591
on x=-53147..-26083,y=6970..32916,z=-73408..-51718
on x=-77684..-58004,y=-54869..-40758,z=2770..29249
on x=19735..29425,y=-78950..-63307,z=-31191..-8035
on x=-78428..-51039,y=19608..39043,z=-34402..-18477
on x=-56128..-50999,y=-33300..-13168,z=-70146..-37841
on x=4625..24363,y=-72098..-35735,z=-55520..-43632
on x=18211..29224,y=-813..8671,z=55446..79680
on x=-97543..-59319,y=-1689..15434,z=-11974..14496
on x=-32530..-10666,y=38930..75291,z=36247..60871
on x=2821..28811,y=62586..94483,z=-32458..-16919
on x=-40471..-31130,y=15938..28151,z=-70608..-59791
on x=-80377..-51104,y=3929..34746,z=-39316..-20065
on x=18571..40190,y=40609..60179,z=53325..73463
on x=-59123..-34702,y=-41372..-20362,z=54097..74083
on x=27777..47040,y=1326..31581,z=61312..91885
on x=16182..33899,y=48556..69646,z=-62089..-48887
on x=19423..49580,y=73346..92185,z=-25981..-1216
on x=-26277..-5823,y=60608..81782,z=19810..40315
on x=-3740..18222,y=51328..69118,z=46024..67347
on x=61030..90135,y=15920..43168,z=21666..24802
on x=50326..65306,y=5266..14340,z=36919..63604
on x=5310..36234,y=54441..74397,z=36549..58654
on x=65906..78863,y=9241..23849,z=-8344..21536
on x=-51336..-25819,y=-77592..-51550,z=-42622..-16601
on x=-14930..21002,y=-82090..-60472,z=10702..23987
on x=5743..28784,y=-10945..22043,z=-92426..-61633
on x=13167..44835,y=62673..88366,z=-34010..-11866
on x=-41786..-12336,y=-45976..-21266,z=54227..86666
on x=-15296..-5851,y=32340..58916,z=50952..78088
on x=58231..77474,y=38899..66963,z=2286..21453
on x=34298..47885,y=-50220..-29515,z=52025..72794
on x=314..25867,y=-46240..-36063,z=62727..83694
on x=1566..23330,y=-32937..-8389,z=60722..82903
on x=-12183..17438,y=55290..69189,z=42385..48070
on x=-32196..-9927,y=64847..78357,z=-18881..-5668
on x=52235..70519,y=-47010..-13939,z=37418..54950
on x=14596..31606,y=-5098..24298,z=-75390..-57730
on x=-81826..-70884,y=-7781..7128,z=29175..37932
on x=-3961..1447,y=-16406..-13522,z=75028..83277
on x=-53659..-27045,y=54023..82532,z=-4947..14234
on x=-18759..-4432,y=-27565..-5957,z=-93754..-61405
on x=35737..47192,y=-45376..-13832,z=-79008..-44111
on x=17458..47717,y=25400..38583,z=66049..68208
on x=46369..62125,y=19606..30098,z=-60376..-38742
on x=-30489..-12220,y=53075..64667,z=38322..56335
on x=11289..35163,y=-86798..-60841,z=11783..33096
on x=23247..46479,y=-10921..25050,z=-74247..-60455
on x=-76004..-51368,y=-34942..-11954,z=42456..53704
on x=30577..51035,y=-23595..-9718,z=57322..88234
on x=-40586..-36333,y=-20814..11706,z=-78705..-67139
on x=-69886..-41253,y=36030..47957,z=31700..41099
on x=-1811..29584,y=57511..64403,z=48452..69327
on x=49575..62476,y=-71712..-39970,z=-9522..14866
on x=-62585..-45638,y=27823..42900,z=24912..51864
on x=-38462..-27078,y=-45237..-33022,z=-57010..-41264
on x=-33740..788,y=28581..49280,z=-81596..-50891
on x=59659..72627,y=-45902..-13557,z=26557..45364
on x=-35477..-27321,y=49189..57428,z=-65073..-33433
on x=9314..28986,y=59876..82188,z=13857..37340
on x=14526..45789,y=-22174..-3326,z=-83651..-71026
on x=59208..79626,y=-64642..-32857,z=-39753..-7836
on x=-42841..-18892,y=-24500..821,z=63034..74498
on x=28315..39316,y=-82251..-57440,z=-4592..34415
on x=15732..28291,y=55208..78787,z=-65795..-47224
on x=-3181..22727,y=73186..84659,z=-41006..-12696
on x=67108..84193,y=-61865..-30444,z=-6936..20127
on x=37203..55463,y=37799..60788,z=-43586..-17507
on x=-64888..-30421,y=47717..81276,z=20635..35000
on x=-7187..23954,y=26791..50806,z=64428..91762
on x=-81502..-62792,y=-58925..-37488,z=-25240..-2792
on x=56503..75489,y=-56721..-31683,z=11933..27761
on x=-31741..-24152,y=61471..88987,z=-32693..-16427
on x=61045..82028,y=-35959..-5039,z=36339..47547
on x=59590..77830,y=16402..40339,z=28558..54408
on x=-12425..12838,y=-76235..-47466,z=-49695..-42676
on x=10031..30645,y=10195..33251,z=-80528..-67720
on x=-12661..14184,y=48274..57691,z=-69957..-58486
on x=-83574..-54543,y=-43918..-13070,z=-28757..-2370
on x=-32114..-16011,y=9676..16446,z=-91247..-56549
on x=10721..14570,y=-71783..-40308,z=43930..74074
on x=48148..70761,y=50670..60667,z=-2599..12943
on x=43834..65270,y=-70269..-38156,z=-7709..16384
on x=-59964..-29205,y=18924..50274,z=-73119..-44021
on x=48495..54915,y=-22553..-14496,z=41644..64119
on x=39268..50617,y=36682..42142,z=41229..72946
on x=-28122..-6377,y=-55056..-39090,z=-69009..-54516
on x=-93621..-68687,y=-9578..12245,z=-30738..-8695
on x=60235..92615,y=-14867..1912,z=-43089..-17694
on x=-65434..-61186,y=1226..30216,z=32457..46531
on x=52354..71161,y=17582..32051,z=-55143..-47922
on x=921..28130,y=71968..81659,z=-34181..-9983
on x=39754..52621,y=43940..76220,z=-7815..27000
on x=33121..44374,y=-80759..-56624,z=1578..7093
on x=-67350..-50706,y=-4015..11156,z=-61486..-42495
on x=-88951..-70376,y=-19977..6184,z=-39282..-28276
on x=-7351..6450,y=-70685..-54734,z=38583..48077
on x=-10550..12884,y=14865..18581,z=72847..94169
on x=-87522..-73378,y=-7741..9781,z=3374..24386
on x=-36641..-23959,y=57960..87908,z=-370..16925
on x=-68826..-46421,y=-67244..-39947,z=-7291..9784
on x=73136..80158,y=-23535..-3391,z=-28222..3208
on x=52788..64131,y=4956..20081,z=-61404..-41453
on x=58803..77195,y=-16951..17593,z=25225..47381
on x=22483..31542,y=-79807..-67413,z=8876..34977
on x=-73205..-44687,y=36999..43848,z=-43815..-42178
on x=32904..55296,y=53277..76504,z=-17381..-3633
on x=-13031..-8992,y=60216..77258,z=-68681..-46586
on x=50126..55939,y=-392..5353,z=57066..77702
on x=-74012..-40779,y=47728..75871,z=-18893..-5260
on x=-19593..15913,y=36869..49018,z=-74511..-53236
on x=-78193..-55575,y=-52909..-26471,z=-34844..-20988
on x=-18773..3629,y=-18379..-9158,z=-82255..-62655
on x=-21937..11585,y=55273..77350,z=-54195..-28158
on x=-3670..15727,y=59319..84590,z=-27729..-1093
on x=49093..69345,y=-21873..11819,z=48150..74374
on x=68719..87433,y=-2502..23189,z=21147..21915
on x=-33825..-3773,y=52141..63573,z=-64574..-31898
on x=3428..19434,y=-90823..-66985,z=27028..44260
on x=-34301..-9796,y=-17793..3267,z=64867..86550
on x=23278..56484,y=-71328..-62783,z=-36385..-8377
on x=63230..67678,y=-63391..-36773,z=-14668..6407
on x=-20889..108,y=39026..54854,z=48108..64165
on x=-76076..-60098,y=-33015..-924,z=30448..56620
on x=32321..41839,y=42425..68050,z=28788..53257
on x=-19226..-16041,y=-47428..-28336,z=-81084..-51405
on x=43738..73895,y=-63793..-52652,z=3686..32334
on x=-82735..-62208,y=4507..7692,z=-53719..-44431
on x=-87917..-70050,y=-31249..-10639,z=-34432..-26717
on x=-5128..9123,y=60846..84835,z=-11135..14047
on x=13403..46172,y=-2332..19717,z=-81284..-57202
on x=-79615..-55523,y=-33141..294,z=-65477..-33092
on x=-75359..-40021,y=-74261..-46625,z=-8389..22135
on x=-12873..1788,y=-41162..-26386,z=51626..89423
off x=-27225..-15552,y=-38154..-8879,z=-77461..-67732
off x=49564..63731,y=-836..12849,z=-60941..-40039
on x=28514..51686,y=-42906..-16517,z=-56963..-40559
on x=19595..43347,y=28091..32747,z=51513..70682
on x=5458..26093,y=-65295..-35396,z=48702..58362
on x=-48274..-29233,y=-76739..-60012,z=22307..37761
off x=1981..29250,y=69451..93818,z=17850..31802
on x=-20845..-13182,y=-80720..-75069,z=-12113..-4052
on x=-84418..-68091,y=-847..16955,z=-28792..-2302
off x=51651..71641,y=37297..52569,z=-39477..-21468
off x=50195..81102,y=23860..37050,z=-42925..-30098
off x=-20363..2595,y=-44773..-18061,z=-77784..-51812
on x=36182..72745,y=-70291..-51854,z=-2517..18156
off x=55993..80025,y=12977..31602,z=35059..57916
on x=-41877..-24484,y=-75484..-50529,z=34541..49068
on x=48409..67821,y=21077..33167,z=28289..50138
on x=18922..32553,y=3963..16110,z=67158..92951
off x=71806..77210,y=13012..32895,z=4662..15716
off x=50310..76018,y=-38258..-24396,z=-2714..29857
off x=36680..46142,y=43946..61172,z=41666..55647
off x=59141..69856,y=4726..16581,z=41233..59734
off x=6480..14384,y=72657..97482,z=-9296..9968
on x=-37323..-31832,y=55310..84805,z=7362..39434
off x=50098..60408,y=-59146..-42987,z=-47254..-37048
off x=-56141..-41893,y=-71229..-50117,z=8079..15143
off x=24047..48176,y=-75498..-58141,z=-9941..858
on x=48677..74447,y=-25240..2507,z=38159..44163
on x=-46381..-15738,y=-58574..-51401,z=47893..62053
on x=-69094..-56675,y=-26611..1175,z=34147..51610
on x=-91135..-68359,y=2393..22084,z=-6470..6127
on x=-75176..-51753,y=-43737..-26236,z=-23821..-21458
off x=40130..56481,y=47062..66092,z=12403..26795
on x=-19442..-3859,y=1603..28535,z=-81893..-76349
on x=68514..84937,y=11749..40600,z=1453..18646
on x=31397..64807,y=47112..66595,z=-35934..-17805
on x=46050..82726,y=-42861..-9155,z=-44140..-23164
on x=64539..67300,y=36015..53289,z=-12513..6583
on x=-38212..-15792,y=-89866..-50598,z=17229..28102
on x=48952..71700,y=-26702..2963,z=-67738..-44747
off x=-40567..-17346,y=836..15296,z=66198..82881
off x=-79496..-53221,y=28663..51510,z=-59755..-33079
off x=56644..75529,y=-57084..-35223,z=-41347..-18984
off x=-11853..-1034,y=-89939..-69149,z=-13780..2282
on x=-32489..-5386,y=-62320..-35090,z=-82134..-47767
off x=-29772..-10616,y=-69972..-62475,z=-54451..-22273
on x=-69042..-46601,y=25152..51362,z=-45358..-29985
off x=-83683..-55489,y=-30042..-17753,z=9874..37024
on x=15982..28379,y=-52324..-33719,z=-62153..-44387
on x=-3777..32485,y=27444..45813,z=-79477..-52643
off x=39542..62961,y=-71499..-51266,z=19654..38752
on x=-74710..-56422,y=35786..56047,z=-21539..-2361
on x=58457..85256,y=5602..26335,z=-27853..-9229
off x=-85875..-67682,y=-35597..-16295,z=-11087..4397
off x=45969..69594,y=-56294..-48054,z=-27374..-21652
off x=-923..31648,y=-44761..-34079,z=-72981..-60528
off x=-90391..-75766,y=-26878..-3405,z=-31396..-4444
off x=12653..35073,y=-78898..-67780,z=-39286..-656
off x=46554..73800,y=-59916..-52157,z=16517..29368
off x=36675..71161,y=44680..70416,z=9040..21703
on x=-38556..-12579,y=-51899..-28764,z=57623..67587
off x=7576..30316,y=-76882..-54904,z=38324..63726
off x=-17621..-6661,y=-22654..-14173,z=61108..82174
on x=-84475..-67415,y=-56445..-36516,z=-9462..8039
on x=27375..31781,y=36887..54176,z=-73986..-53953
on x=58467..69570,y=-51872..-47458,z=-44145..-24547
off x=18166..31687,y=60742..80436,z=18086..36497
on x=2746..24218,y=72011..84625,z=-12338..-3553
on x=-5733..10294,y=73220..86751,z=-35430..-26371
off x=42538..60808,y=48612..74747,z=-18176..6236
on x=33990..54525,y=-58978..-48561,z=-54206..-33153
off x=56228..84438,y=1875..34543,z=30179..41306
off x=-88013..-65168,y=-34096..-3171,z=14515..24591
off x=-14357..10420,y=5114..20116,z=77255..86983
off x=-54379..-41812,y=-76536..-47712,z=-10144..14085
off x=-73839..-60871,y=19129..46989,z=-29618..-11780
off x=-81126..-61094,y=-23995..10888,z=39616..61067
off x=-68285..-43192,y=21826..40735,z=31938..55887
on x=-18454..6132,y=28842..38319,z=61158..83662
on x=-56835..-23950,y=712..19239,z=50841..70006
off x=-31563..-5602,y=-18184..5775,z=-83067..-65221
off x=-28384..-11355,y=14487..37943,z=52911..87337
off x=-26436..-19593,y=-21438..4473,z=-84168..-56764
on x=13057..33170,y=55832..91646,z=7567..34062
off x=-86661..-55254,y=-35950..-30351,z=25643..36440
on x=56717..74146,y=9212..37134,z=-36254..-17711
off x=-75466..-58127,y=-9262..11320,z=16113..43634
off x=4059..25327,y=4684..17206,z=-81805..-59786
on x=-64749..-40509,y=-53983..-40482,z=9394..44855
on x=-82416..-70381,y=-26357..-15476,z=-8169..16401
off x=55461..65390,y=-52497..-48799,z=-17789..4935
off x=52182..58303,y=-60261..-46276,z=-29918..-6932
on x=-3204..13051,y=-71258..-52709,z=31463..46671
off x=-57048..-26000,y=-28479..-16272,z=-79051..-64132
off x=-14847..7159,y=11886..27624,z=73031..81749
on x=-21491..6926,y=-13963..-3356,z=-91823..-71558
off x=-30375..-23050,y=-67041..-62754,z=28809..43136
off x=12650..26496,y=-76013..-53741,z=-48247..-30031
on x=59885..81505,y=-29870..-3934,z=-44746..-18470
on x=-79601..-54304,y=-11515..-102,z=-46559..-32436
on x=28991..56756,y=52522..74509,z=-2519..14274
on x=43967..76974,y=20579..47818,z=35014..61786
on x=-77668..-46830,y=15784..54205,z=-42893..-12204
on x=21468..45013,y=-48761..-29087,z=-64106..-43389
on x=57653..72593,y=-46407..-21594,z=30220..43976
off x=-21411..5382,y=-87980..-70719,z=-29569..-9882
on x=31833..38323,y=-27245..1712,z=60098..72097
off x=-55050..-43170,y=19212..34884,z=53931..61809
on x=33284..57411,y=24869..44872,z=49777..65263
on x=49511..73690,y=30455..63341,z=-25761..-1931
on x=-56947..-35531,y=-5760..2162,z=-65335..-44499
on x=-31615..-13487,y=62549..80851,z=-19495..-9945
off x=-15929..2976,y=-63150..-37402,z=-63872..-59321
off x=-28016..-3640,y=65236..93714,z=-29535..-3028
off x=6332..35885,y=-81206..-70750,z=-21026..-7784
on x=-59092..-30752,y=-6217..13634,z=59523..67038
off x=21892..47757,y=56813..69606,z=-49014..-33060
on x=-80300..-55488,y=8779..35520,z=9678..24899
off x=17810..41524,y=-9833..22038,z=59887..85929
off x=-61853..-46732,y=10193..32326,z=51857..70253
off x=-12705..13662,y=-72775..-51627,z=50857..70094
off x=-41608..-11921,y=46052..66377,z=-56256..-43823
off x=54753..85613,y=-27149..30,z=19773..38641
off x=56339..82326,y=29173..54903,z=-24544..-4701
off x=-39252..-26157,y=-28289..-5059,z=53458..70740
off x=-34933..-14519,y=26344..61175,z=-69433..-54095
off x=-28562..-5801,y=-33822..-18327,z=-93310..-64118
on x=22032..32089,y=-37280..-33687,z=47358..81675
off x=-3997..12192,y=-86463..-63044,z=23027..42421
off x=-44709..-11067,y=65083..71004,z=21613..42575
on x=47266..65381,y=-12156..-2218,z=35715..58574
off x=25971..45782,y=25963..39357,z=57518..78074
off x=52392..77418,y=27203..36735,z=-34339..-27294
off x=35818..43659,y=-73358..-36718,z=26256..44571
off x=57420..84570,y=-4748..7263,z=21309..40222
on x=-66907..-35908,y=-6572..13327,z=-77072..-48128
off x=40968..64348,y=-35386..-11011,z=40389..65932
off x=-19380..9994,y=-94512..-75264,z=-30274..-2465
on x=-68633..-42647,y=-60792..-41086,z=-10057..11001
off x=15803..44938,y=-76481..-60364,z=7393..10029
on x=31454..55860,y=4734..15203,z=-73298..-51876
on x=-49443..-29933,y=37844..69928,z=-49896..-28648
off x=38003..41546,y=-9021..957,z=-88704..-51755
off x=-29893..-5790,y=-55218..-26469,z=-72964..-58299
on x=65257..70448,y=-39324..-19561,z=-40548..-30625
on x=-27676..4011,y=-72845..-57444,z=-61523..-39162
off x=27409..55236,y=-81664..-58257,z=6409..24320
off x=-54622..-37546,y=-76337..-51963,z=-40336..-17952
on x=-81142..-71424,y=17540..39356,z=-1618..21877
off x=19498..53372,y=45802..61211,z=41770..65870
off x=-82966..-63210,y=-48223..-19081,z=17795..29938
on x=44060..55106,y=6420..26586,z=-73703..-63385
on x=-27925..-25840,y=-77015..-59666,z=23076..49124
on x=25978..58390,y=-5183..27351,z=-72668..-61659
on x=27577..52858,y=18384..33571,z=-81189..-45422
off x=1644..13135,y=-91350..-74691,z=-23438..-13621
on x=-63641..-48151,y=-68761..-43746,z=-40994..-14636
on x=-64..22739,y=-78599..-60752,z=31671..46606
off x=-6745..1223,y=79204..97644,z=-15673..-6081
off x=-84361..-68718,y=-15800..11011,z=-21725..-5663
off x=1796..26791,y=-22982..6592,z=65332..86505
off x=14782..32463,y=12354..31832,z=67300..93588
on x=-26476..-3931,y=-37541..-17510,z=58109..85942
on x=-45165..-18966,y=-31631..-24406,z=66270..87004
off x=6739..28073,y=-28783..-11300,z=63576..82033
on x=20516..26876,y=8768..34065,z=-89789..-66267
on x=-63235..-27908,y=25761..34821,z=-61386..-47821
on x=-47275..-44019,y=-35270..-20042,z=-65305..-45883
off x=-23302..-6090,y=-97547..-65686,z=-18174..-10580
on x=-74984..-51332,y=-44306..-28216,z=-54625..-31193
off x=-6996..20362,y=-81742..-74178,z=-11750..8850
on x=-81824..-66689,y=-1857..23095,z=28136..42645
off x=7523..27640,y=-4334..33200,z=60500..80565
off x=-56150..-39231,y=42506..63912,z=24698..41176
off x=-44712..-23933,y=-1506..31445,z=-87191..-51579
on x=-18333..-7407,y=31656..66279,z=-75095..-54626
off x=38069..68642,y=22516..48066,z=-58252..-38667
off x=76196..87980,y=-12789..20543,z=16805..30891
on x=63074..81067,y=-27548..-2975,z=-15959..5121
on x=51566..64864,y=-17851..-2787,z=53602..69143
off x=20105..57667,y=-63728..-42876,z=-56624..-30001
on x=-79640..-60288,y=7052..25560,z=-42051..-15733
on x=30123..36836,y=-44255..-29065,z=-70757..-44923
off x=-46702..-19941,y=59273..73836,z=-58512..-24825
on x=-81077..-62784,y=26041..49564,z=-19365..13039
off x=68458..87158,y=-35804..-3990,z=-16507..18280
off x=13150..22689,y=-69760..-59804,z=-44281..-19735
off x=-46513..-20778,y=-4643..20634,z=63800..73864
on x=28735..52099,y=50635..74355,z=-49877..-24524
on x=-10794..1461,y=-30724..1553,z=77152..84474
on x=-76055..-52390,y=-38304..-20232,z=-55132..-35931
on x=-5553..28712,y=26277..45688,z=-77180..-59776
on x=-2740..5090,y=-88623..-77004,z=-36432..-14458
on x=-17442..14258,y=-89716..-69565,z=-10119..13330
off x=-67044..-38964,y=-20692..8375,z=-70882..-47159
off x=69935..80127,y=-51311..-22903,z=-28871..-14058
off x=-22967..-14296,y=51177..66674,z=40850..55173
on x=-17210..-6464,y=59742..92888,z=-31822..-16392
off x=26208..43513,y=-27801..-8056,z=49432..80324
on x=31699..37219,y=-36521..-23135,z=61018..77965
on x=-13575..7002,y=-33410..-19901,z=59130..95383""".splitlines()]

# find_on_count(input)

# Experiment 1: Is our first approach feasible, even with 10 filters?
# If so, we can use the subdivision model.
# import cProfile
# cProfile.run("find_cube_on_count(input[100:110])")
# Result 1: With 10 filters it still takes a long time.
# Looks like we can't use the subdivision model.
# Have to *sigh* merge regions.

import cProfile
# find_cube_on_count(input[0:3])
# cProfile.run("find_cube_on_count(input[0:20])")
# cProfile.run("find_cube_on_count(input[20:110])")
#find_cube_on_count(input[0:5])
# find_cube_on_count(input[20:22])

find_cube_on_count(input[0:20]) # 1198059 is too high; why?
# 1161611382652688 is too low
# find_cube_on_count(input)