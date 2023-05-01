"""vicregBiological_globalDefs.py

# Author:
Richard Bruce Baxter - Copyright (c) 2022-2023 Baxter AI (baxterai.com)

# License:
MIT License

# Installation:
conda create -n pytorchsenv
source activate pytorchsenv
conda install python
pip install datasets
pip install torch
pip install lovely-tensors
pip install torchmetrics

# Usage:
source activate pytorchsenv

	###Trial vicreg code (test only based on README.md);
	
	#Single-node local training
	python vicreg/main_vicreg.py --data-dir datasets/imagenette2-320 --exp-dir out/exp --arch resnet50 --epochs 10 --batch-size 64 --base-lr 0.3
		NOTUSED; python vicreg/main_vicreg.py --data-dir datasets/tiny-imagenet-200 --exp-dir out/exp --arch resnet50 --epochs 100 --batch-size 64 --base-lr 0.3

	#Linear evaluation
	python vicreg/evaluate.py --data-dir datasets/imagenette2-320 --pretrained out/exp/resnet50.pth --exp-dir ./out/exp --epochs 10 --batch-size 64 --lr-head 0.02

		##Test out-of-distribution class classification after Backprop vs VICReg model backbone training;
		- expbp: Resnet-50 top 1 performance trained on 50% of images with Backprop, evaluate top-1 performance when only training final layer [ie linear classifier] on 100% images
		- expvr: Resnet-50 top 1 performance trained on 50% of images with VICREG, evaluate top-1 performance when only training final layer [ie linear classifier] on 100% images

		###expbp (backprop 50% training, 100% linear eval);

		#do not need to train, just generate model (expbp/resnet50.pth)
		python vicreg/main_vicreg.py --data-dir datasets/imagenette2-320-half --exp-dir out/expbp --arch resnet50 --epochs 1 --batch-size 64 --base-lr 0.3

		#Backprop training with 50% classes
		python vicreg/evaluate.py --data-dir datasets/imagenette2-320-half --pretrained out/expbp/resnet50.pth --exp-dir out/expbp --batch-size 64 --weights finetune --train-perc 100 --epochs 100 --lr-backbone 0.3 --weight-decay 0
			#FUTURE: consider using full imagenette2-320 dataset but train-perc parameter=50
		rm expbp/checkpoint.pth
		
		#Linear evaluation with 100% classes
		python vicreg/evaluate.py --data-dir datasets/imagenette2-320 --pretrained out/expbp/resnet50eval.pth --exp-dir out/expbp --batch-size 64 --weights freeze --lr-head 0.02

		###expvr (vicreg 50% training, 100% linear eval);

		#VICReg hidden layer training with 50% classes
		python vicreg/main_vicreg.py --data-dir datasets/imagenette2-320-half --exp-dir out/expvr --batch-size 64 --arch resnet50 --epochs 100 --base-lr 0.3
			#--train-perc 100 [implied]

		#Linear evaluation with 100% classes
		python vicreg/evaluate.py --data-dir datasets/imagenette2-320 --pretrained out/expvr/resnet50.pth --exp-dir out/expvr --batch-size 64 --weights freeze --lr-head 0.02

# Description:
vicreg biological globalDefs

"""

import torch as pt
import torch.nn as nn

vicregBiologicalMods = False

#initialise (dependent vars);
trainGreedy = False
usePositiveWeights = False
normaliseActivationSparsity = False
trainGreedyIndependentBatchNorm = False
smallInputImageSize = False

if(vicregBiologicalMods):
	usePositiveWeights = True
	if(usePositiveWeights):
		usePositiveWeightsClampModel = True	#clamp entire model weights to be positive (rather than per layer); currently required
		normaliseActivationSparsity = True	#perform layer norm instead of batch norm (default resnet model setting)
	trainGreedy = True
	if(trainGreedy):
		applyIndependentLearningForDownsample = False	#optional	#apply independent learning for downsample (conv1x1)	#not downsample is only used for first block in l1
		learningRateLocal = 0.005
		debugTrainGreedy = False
		if(not normaliseActivationSparsity):
			trainGreedyIndependentBatchNorm = True	#default:True	#TODO: perform experimentation to check performance difference (is perfect batch norm required?)
		smallInputImageSize = True	#required for vicregBiologicalMods:trainGreedy due to cov_x = (x.T @ x) operation on large image size
	else:
		smallInputImageSize = True	#optional (not required); can be used to ensure that experiments are equivalent [to trainGreedy]

if(smallInputImageSize):
	imageWidth = 32	#needs to be sufficiently high such that convolutions do not prematurely converge	#cannot be too high else will run out of RAM
	#not required: use datasetTinyImagenet, as imagenet/imagenette images will be downsampled
else:
	imageWidth = 224	#use imagenet [1000 classes]/imagenette [10 class]


def printe(str):
	print(str)
	exit()
	
useLovelyTensors = True
if(useLovelyTensors):
	import lovely_tensors as lt
	lt.monkey_patch()
else:
	pt.set_printoptions(profile="full")
	pt.set_printoptions(sci_mode=False)

class sequentialMultiInput(nn.Sequential):
	def forward(self, *inputs):
		for module in self._modules.values():
			if type(inputs) == tuple:
				inputs = module(*inputs)
			else:
				inputs = module(inputs)
		return inputs

'''
class sequentialMultiInput(nn.Sequential):
	def forward(self, *input):
		for module in self._modules.values():
			input = module(*input)
		return input
'''		
