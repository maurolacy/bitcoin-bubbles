bestSpan <- 0.088
bubbleScaled <- read.csv("bubbleScaled-1.tsv", sep='\t', header=TRUE)
bubble.lo <- loess(value ~ time, bubbleScaled, degree=1, span=bestSpan)
bubble.lo$enp
predict(bubble.lo, 1, se=TRUE)$df
