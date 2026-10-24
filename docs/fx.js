/* shared helpers for the per-project identity scripts (no dependencies) */
(function(){'use strict';
var d=document,R=d.documentElement;
var FX=window.FX={
 reduce:!!(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches),
 $:function(s,c){return(c||d).querySelector(s)},
 $$:function(s,c){return Array.prototype.slice.call((c||d).querySelectorAll(s))},
 mouse:{x:-1e3,y:-1e3,px:.5,py:.5},
 /* add .rv and reveal on scroll */
 reveal:function(sel,cls){cls=cls||'in';var els=FX.$$(sel);els.forEach(function(e){e.classList.add('rv')});
  if(FX.reduce||!('IntersectionObserver' in window)){els.forEach(function(e){e.classList.add(cls)});return}
  var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){x.target.classList.add(cls);io.unobserve(x.target)}})},{rootMargin:'0px 0px -6% 0px'});els.forEach(function(e,i){e.style.setProperty('--i',i%6);io.observe(e)})},
 /* canvas loop: sizes to its box, pauses offscreen / hidden tab; draw(ctx,w,h,t,dt,m) with m = mouse in canvas px */
 loop:function(cv,draw,o){o=o||{};var ctx=cv.getContext('2d'),w=0,h=0,dpr=1,raf=0,on=false,vis=true,last=0,t0=performance.now(),m={x:-1e3,y:-1e3,in:false};
  function size(){var r=cv.getBoundingClientRect();w=r.width;h=r.height;dpr=Math.min(o.dpr||2,window.devicePixelRatio||1);cv.width=Math.max(1,Math.round(w*dpr));cv.height=Math.max(1,Math.round(h*dpr));ctx.setTransform(dpr,0,0,dpr,0,0);if(o.resize)o.resize(w,h)}
  function fr(now){if(!on)return;var t=(now-t0)/1000,dt=Math.min(.05,(now-last)/1000||.016);last=now;ctx.setTransform(dpr,0,0,dpr,0,0);draw(ctx,w,h,t,dt,m);raf=requestAnimationFrame(fr)}
  function go(){if(on||FX.reduce||d.hidden||!vis)return;on=true;last=performance.now();raf=requestAnimationFrame(fr)}
  function stop(){on=false;cancelAnimationFrame(raf)}
  size();addEventListener('resize',function(){size();if(!on){ctx.setTransform(dpr,0,0,dpr,0,0);draw(ctx,w,h,0,0,m)}});
  var host=o.host||cv.parentElement;host.addEventListener('pointermove',function(e){var r=cv.getBoundingClientRect();m.x=e.clientX-r.left;m.y=e.clientY-r.top;m.in=true},{passive:true});host.addEventListener('pointerleave',function(){m.in=false;m.x=m.y=-1e3});
  if(FX.reduce){draw(ctx,w,h,o.still||2,0,m)}else{
   if('IntersectionObserver' in window)new IntersectionObserver(function(es){vis=es[0].isIntersecting;vis?go():stop()},{threshold:0}).observe(cv);else go();
   d.addEventListener('visibilitychange',function(){d.hidden?stop():go()});draw(ctx,w,h,0,0,m)}
  return{size:size,draw:function(){draw(ctx,w,h,(performance.now()-t0)/1000,0,m)},ctx:ctx};},
 /* create an absolutely positioned canvas as the first child of host */
 layer:function(host,cls){var cv=d.createElement('canvas');cv.className='fx '+(cls||'');cv.setAttribute('aria-hidden','true');cv.setAttribute('role','presentation');if(getComputedStyle(host).position==='static')host.style.position='relative';host.insertBefore(cv,host.firstChild);return cv},
 css:function(n){return getComputedStyle(R).getPropertyValue(n).trim()},
 rnd:function(a,b){return a+Math.random()*(b-a)},
 theme:function(){return R.getAttribute('data-theme')==='dark'?'dark':'light'}
};
addEventListener('pointermove',function(e){FX.mouse.x=e.clientX;FX.mouse.y=e.clientY;FX.mouse.px=e.clientX/innerWidth;FX.mouse.py=e.clientY/innerHeight},{passive:true});
R.classList.add('fxjs');
})();

(function(){var body=document.body;var tl=document.createElement('div');tl.className='tiles';tl.setAttribute('aria-hidden','true');body.insertBefore(tl,body.firstChild);
var cv=document.createElement('canvas');cv.className='ink';cv.setAttribute('aria-hidden','true');body.insertBefore(cv,body.firstChild);
var tr=[],blots=[],pen={x:0,y:0,vx:0,vy:0,ph:Math.random()*9,u:0},lastM=0;
function nibseg(c,a,b,wid,col,al){var ang=-Math.PI/4,dx=Math.cos(ang)*wid/2,dy=Math.sin(ang)*wid/2;c.globalAlpha=al;c.fillStyle=col;c.beginPath();c.moveTo(a.x-dx,a.y-dy);c.lineTo(a.x+dx,a.y+dy);c.lineTo(b.x+dx,b.y+dy);c.lineTo(b.x-dx,b.y-dy);c.closePath();c.fill()}
cv.addEventListener('pointerdown',function(e){var r=cv.getBoundingClientRect();blots.push({x:e.clientX-r.left,y:e.clientY-r.top,t:performance.now(),r:6+Math.random()*10,sp:Array.from({length:7},function(){return[Math.random()*6.3,8+Math.random()*26,1+Math.random()*3]})})});
FX.loop(cv,function(c,w,h,t,dt,m){var D=FX.theme()==='dark',col=D?'#e9c46a':'#10334a',teal=D?'#2fd0c8':'#0a7e84';c.clearRect(0,0,w,h);
 var now=performance.now(),user=m.in&&now-lastM<1800;
 if(m.in){if(m.x!==pen.lx||m.y!==pen.ly){lastM=now;pen.lx=m.x;pen.ly=m.y}}
 var tx,ty;
 if(user){tx=m.x;ty=m.y}else{/* autonomous calligraphy: a looping flourish with an elongated "alef/lam" rhythm */pen.u+=dt*.85;var u=pen.u,A=w*.42;tx=w*.5+Math.sin(u*.9)*A+Math.sin(u*2.7)*w*.04;ty=h*.5+Math.sin(u*1.8+Math.sin(u*.45)*2)*h*.26+Math.cos(u*3.3)*h*.05}
 var k=user?.35:.12;pen.vx=(tx-pen.x)*k;pen.vy=(ty-pen.y)*k;if(!tr.length){pen.x=tx;pen.y=ty}
 var px=pen.x,py=pen.y;pen.x+=pen.vx;pen.y+=pen.vy;var sp=Math.hypot(pen.vx,pen.vy);tr.push({x:pen.x,y:pen.y,w:Math.max(2,Math.min(15,14-sp*.6)),t:t,c:user?teal:col});if(tr.length>340)tr.shift();
 for(var i=1;i<tr.length;i++){var a=tr[i-1],b=tr[i],age=t-b.t;var al=Math.max(0,1-age/(user?5:7));nibseg(c,a,b,b.w,b.c,al*.88)}c.globalAlpha=1;
 /* nib tip */ c.fillStyle=teal;c.beginPath();c.arc(pen.x,pen.y,2.5,0,6.3);c.fill();
 blots=blots.filter(function(b){return now-b.t<4000});blots.forEach(function(b){var u=Math.min(1,(now-b.t)/350),al=1-Math.max(0,(now-b.t-2000)/2000);c.globalAlpha=al*.85;c.fillStyle=col;c.beginPath();c.arc(b.x,b.y,b.r*(.4+u*.6),0,6.3);c.fill();b.sp.forEach(function(s){c.beginPath();c.arc(b.x+Math.cos(s[0])*s[1]*u,b.y+Math.sin(s[0])*s[1]*u,s[2],0,6.3);c.fill()});c.globalAlpha=1});
},{still:6,dpr:1.5,host:document.body});
FX.reveal('.lx-card,.lx-head,.rg,.lx-cta');
})();
