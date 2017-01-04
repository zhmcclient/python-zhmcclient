#!/bin/sh
echo "Example script demonstrating zhmc CLI partition commands."

eval $(zhmc -h $HMC_HOST -u $HMC_USER session create)
zhmc cpc list
out=$(zhmc -o json cpc show $CPC_NAME)
dpm=$(echo "$out" | python -c "import json,sys; obj=json.load(sys.stdin); print(obj['dpm-enabled'])")
if [ $dpm != "True" ]
then
   echo "CPC $CPC_NAME is not in DPM mode."
   eval $(zhmc session delete)
   exit 2
else
   echo "CPC $CPC_NAME is in DPM mode."
fi
zhmc partition list $CPC_NAME
zhmc partition create $CPC_NAME \
   --name $PART_NAME \
   --description "This is a partition created by zhmc." \
   --cp-processors 1 \
   --initial-memory 4096 \
   --maximum-memory 4096 \
   --processor-mode shared \
#   --boot-device test-operating-system
zhmc partition show $CPC_NAME $PART_NAME
zhmc partition start $CPC_NAME $PART_NAME
zhmc partition stop $CPC_NAME $PART_NAME
zhmc partition delete $CPC_NAME $PART_NAME --yes
eval $(zhmc session delete)
