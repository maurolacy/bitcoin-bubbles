loess.aic <- function (x) {
	if (!(inherits(x,"loess"))) stop("Error: argument must be a loess object")
	# extract values from loess object
	span <- x$pars$span
	n <- x$n
	traceL <- x$trace.hat
	sigma2 <- sum( x$residuals^2 ) / (n-1)
	delta1 <- x$one.delta
	delta2 <- x$two.delta
	enp <- x$enp

	aicc <- log(sigma2) + 1 + 2* (2*(traceL+1)) / (n-traceL-2)
#	aicc1<- n*log(sigma2) + n* ( (delta1/(delta2*(n+enp)))/(delta1^2/delta2)-2 )
	aicc1<- n*log(sigma2) + n* ( (delta1/delta2)*(n+enp)/(delta1^2/delta2)-2 )
	gcv  <- n*sigma2 / (n-traceL)^2
	
	result <- list(span=span, target=enp, aicc=aicc, aicc1=aicc1, gcv=gcv)
	return(result)
}

loess.aicTarget <- function (x) {
	if (!(inherits(x,"loess"))) stop("Error: argument must be a loess object")
	# extract values from loess object
	target <- x$pars$enp.target
	n <- x$n
	traceL <- x$trace.hat
	sigma2 <- sum( x$residuals^2 ) / (n-1)
	delta1 <- x$one.delta
	delta2 <- x$two.delta
	enp <- x$enp

	aicc <- log(sigma2) + 1 + 2* (2*(traceL+1)) / (n-traceL-2)
	aicc1<- n*log(sigma2) + n* ( (delta1/delta2)*(n+enp)/(delta1^2/delta2)-2 )
	gcv  <- n*sigma2 / (n-traceL)^2
	
	result <- list(target=target, aicc=aicc, aicc1=aicc1, gcv=gcv)
	return(result)
}

bestLoess <- function(model, criterion=c("aicc", "aicc1", "gcv"), spans=c(.05, .95)) {
	criterion <- match.arg(criterion)
	f <- function(span) {
    mod <- update(model, span=span)
    loess.aic(mod)[[criterion]]
	}
	result <- optimize(f, spans)
	list(span=result$minimum, criterion=result$objective)
}

bestLoessTarget <- function(model, criterion=c("aicc", "aicc1", "gcv"), targets=c(3, 5)) {
	criterion <- match.arg(criterion)
	f <- function(target) {
    mod <- update(model, enp.target=target)
    loess.aicTarget(mod)[[criterion]]
	}
	result <- optimize(f, targets)
	list(target=result$minimum, criterion=result$objective)
}
