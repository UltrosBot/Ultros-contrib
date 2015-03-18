// Bootstrap tour stuff.

tours = {}

var createOrGetTour = function(name) {
    if (name in tours) {
        return tours[name];
    } else {
        tours[name] = new Tour();
        return tours[name];
    }
}

var addTourStep = function(name, step) {
    step.animation = false;
    tours[name].addStep(step);
}

var startTour = function(name) {
    tours[name].init();
    tours[name].restart();
}

var endTour = function(name) {
    tours[name].end();
}

createOrGetTour("global");
createOrGetTour("page");
