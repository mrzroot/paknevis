(function(){var body=document.body;var tl=document.createElement('div');tl.className='tiles';tl.setAttribute('aria-hidden','true');body.insertBefore(tl,body.firstChild);
var cv=document.createElement('canvas');cv.className='ink';cv.setAttribute('aria-hidden','true');body.insertBefore(cv,body.firstChild);
var tr=[],blots=[],pen={x:0,y:0,vx:0,vy:0,ph:Math.random()*9,u:0},lastM=0;
function nibseg(c,a,b,wid,col,al){var ang=-Math.PI/4,dx=Math.cos(ang)*wid/2,dy=Math.sin(ang)*wid/2;c.globalAlpha=al;c.fillStyle=col;c.beginPath();c.moveTo(a.x-dx,a.y-dy);c.lineTo(a.x+dx,a.y+dy);c.lineTo(b.x+dx,b.y+dy);c.lineTo(b.x-dx,b.y-dy);c.closePath();c.fill()}
cv.addEventListener('pointerdown',function(e){var r=cv.getBoundingClientRect();blots.push({x:e.clientX-r.left,y:e.clientY-r.top,t:performance.now(),r:6+Math.random()*10,sp:Array.from({length:7},function(){return[Math.random()*6.3,8+Math.random()*26,1+Math.random()*3]})})});
FX.loop(cv,function(c,w,h,t,dt,m){var D=FX.theme()==='dark',col=D?'#e9c46a':'#10334a',teal=D?'#e07a4f':'#84260a';c.clearRect(0,0,w,h);
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
