bubbleScaled <- read.csv("bubbleScaled.tsv", sep='\t', header = TRUE)
n <- dim(bubbleScaled)[1]
n
bestBandwidth <- 1250
bubble.lo <- loess(value ~ time, bubbleScaled, degree=1, span=bestBandwidth/n)
bubble.lo
predict(bubble.lo, 1, se=TRUE)

res_aicc <- bestLoess(bubble.lo, criterion=c("aicc"), spans=c(1:10 * 0.001))
res_aicc
bestSpan <- 0.104576
bubble.lo <- loess(value ~ time, bubbleScaled, degree=1, span=bestSpan)
bubble.lo
predict(bubble.lo, 1, se=TRUE)
