// A loading indicator only observes requests; it never writes checklist data.
const originalApi=api;let requestsInFlight=0;
api=async function(...args){requestsInFlight++;$('networkProgress').hidden=false;document.body.setAttribute('aria-busy','true');try{return await originalApi(...args)}finally{requestsInFlight--;if(!requestsInFlight){$('networkProgress').hidden=true;document.body.removeAttribute('aria-busy')}}};
