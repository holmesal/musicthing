'''
Calculate:
1. Tickets per band (to win)
2. If the contest is over
'''
import math

capacity = 200
num_bands = 4
nominal_min_tpb = 40 # tickets per band


min_global_tickets = num_bands*nominal_min_tpb
extra_tickets_available = capacity-min_global_tickets

bands = [50,
		50,
		50,
		25,
		20,
		15,
		10
		]

top_bands = bands[:4]
print 'top bands',top_bands
total_max_tickets = sum(top_bands)
if total_max_tickets == capacity:
	print 'at capacity'
else:
	print 'max possible ticket sales',total_max_tickets
	#for n in top_bands:
	#	print n-nominal_min_tpb
	extra_tickets_sold = [count-nominal_min_tpb for count in top_bands if count > nominal_min_tpb]
	print 'extra tickets',extra_tickets_sold
	total_overflow = sum(extra_tickets_sold) - extra_tickets_available
	if total_overflow > 0:
		print 'total overflow',total_overflow
		tpb_reduction = int(math.ceil(float(total_overflow)/float(num_bands)))
		print 'tpb reduction',tpb_reduction
		min_tpb = nominal_min_tpb - tpb_reduction
	else:
		min_tpb = nominal_min_tpb
print 'min tpb',min_tpb
	
#overflow_remaining = sum([n-nominal_min_tpb for n in top_bands])
#print overflow_remaining