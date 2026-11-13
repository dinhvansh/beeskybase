var Qo=0,Ba=1,jo=2;var es=1,el=2,Ti=3,xn=0,Tt=1,rn=2,an=0,qn=1,za=2,Va=3,ka=4,tl=5,In=100,nl=101,il=102,sl=103,rl=104,al=200,ol=201,ll=202,cl=203,Ls=204,Ds=205,hl=206,ul=207,dl=208,fl=209,pl=210,ml=211,gl=212,_l=213,xl=214,sr=0,rr=1,ar=2,Yn=3,or=4,lr=5,cr=6,hr=7,Ga=0,vl=1,yl=2,Jt=0,Ha=1,Wa=2,Xa=3,qa=4,Ya=5,Za=6,Ja=7;var $a=300,Nn=301,jn=302,ur=303,dr=304,ts=306,Us=1e3,en=1001,Ns=1002,gt=1003,Ml=1004;var ns=1005;var _t=1006,fr=1007;var Fn=1008;var Bt=1009,Ka=1010,Qa=1011,Ei=1012,pr=1013,$t=1014,Kt=1015,on=1016,mr=1017,gr=1018,wi=1020,ja=35902,eo=35899,to=1021,no=1022,Ht=1023,tn=1026,On=1027,io=1028,_r=1029,ei=1030,xr=1031;var vr=1033,is=33776,ss=33777,rs=33778,as=33779,yr=35840,Mr=35841,Sr=35842,br=35843,Ar=36196,Tr=37492,Er=37496,wr=37488,Cr=37489,Rr=37490,Ir=37491,Pr=37808,Lr=37809,Dr=37810,Ur=37811,Nr=37812,Fr=37813,Or=37814,Br=37815,zr=37816,Vr=37817,kr=37818,Gr=37819,Hr=37820,Wr=37821,Xr=36492,qr=36494,Yr=36495,Zr=36283,Jr=36284,$r=36285,Kr=36286;var Oi=2300,Fs=2301,Ps=2302,La=2400,Da=2401,Ua=2402;var Sl=3200;var bl=0,Al=1,Mn="",bt="srgb",Zn="srgb-linear",Bi="linear",Xe="srgb";var Xn=7680;var Na=519,Tl=512,El=513,wl=514,Qr=515,Cl=516,Rl=517,jr=518,Il=519,Fa=35044;var so="300 es",Zt=2e3,zi=2001;function ro(i){for(let e=i.length-1;e>=0;--e)if(i[e]>=65535)return!0;return!1}function _c(i){return ArrayBuffer.isView(i)&&!(i instanceof DataView)}function Vi(i){return document.createElementNS("http://www.w3.org/1999/xhtml",i)}function Pl(){let i=Vi("canvas");return i.style.display="block",i}var No={},vi=null;function ao(...i){let e="THREE."+i.shift();vi?vi("log",e,...i):console.log(e,...i)}function Ce(...i){let e="THREE."+i.shift();vi?vi("warn",e,...i):console.warn(e,...i)}function Ee(...i){let e="THREE."+i.shift();vi?vi("error",e,...i):console.error(e,...i)}function yi(...i){let e=i.join(" ");e in No||(No[e]=!0,Ce(...i))}function Ll(i,e,t){return new Promise(function(n,s){function r(){switch(i.clientWaitSync(e,i.SYNC_FLUSH_COMMANDS_BIT,0)){case i.WAIT_FAILED:s();break;case i.TIMEOUT_EXPIRED:setTimeout(r,t);break;default:n()}}setTimeout(r,t)})}var vn=class{addEventListener(e,t){this._listeners===void 0&&(this._listeners={});let n=this._listeners;n[e]===void 0&&(n[e]=[]),n[e].indexOf(t)===-1&&n[e].push(t)}hasEventListener(e,t){let n=this._listeners;return n===void 0?!1:n[e]!==void 0&&n[e].indexOf(t)!==-1}removeEventListener(e,t){let n=this._listeners;if(n===void 0)return;let s=n[e];if(s!==void 0){let r=s.indexOf(t);r!==-1&&s.splice(r,1)}}dispatchEvent(e){let t=this._listeners;if(t===void 0)return;let n=t[e.type];if(n!==void 0){e.target=this;let s=n.slice(0);for(let r=0,a=s.length;r<a;r++)s[r].call(this,e);e.target=null}}},xt=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"];var ca=Math.PI/180,Os=180/Math.PI;function os(){let i=Math.random()*4294967295|0,e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,n=Math.random()*4294967295|0;return(xt[i&255]+xt[i>>8&255]+xt[i>>16&255]+xt[i>>24&255]+"-"+xt[e&255]+xt[e>>8&255]+"-"+xt[e>>16&15|64]+xt[e>>24&255]+"-"+xt[t&63|128]+xt[t>>8&255]+"-"+xt[t>>16&255]+xt[t>>24&255]+xt[n&255]+xt[n>>8&255]+xt[n>>16&255]+xt[n>>24&255]).toLowerCase()}function Be(i,e,t){return Math.max(e,Math.min(t,i))}function xc(i,e){return(i%e+e)%e}function ha(i,e,t){return(1-t)*i+t*e}function Li(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return i/4294967295;case Uint16Array:return i/65535;case Uint8Array:return i/255;case Int32Array:return Math.max(i/2147483647,-1);case Int16Array:return Math.max(i/32767,-1);case Int8Array:return Math.max(i/127,-1);default:throw new Error("Invalid component type.")}}function Ct(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return Math.round(i*4294967295);case Uint16Array:return Math.round(i*65535);case Uint8Array:return Math.round(i*255);case Int32Array:return Math.round(i*2147483647);case Int16Array:return Math.round(i*32767);case Int8Array:return Math.round(i*127);default:throw new Error("Invalid component type.")}}var Je=class i{constructor(e=0,t=0){i.prototype.isVector2=!0,this.x=e,this.y=t}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,t){return this.x=e,this.y=t,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){let t=this.x,n=this.y,s=e.elements;return this.x=s[0]*t+s[3]*n+s[6],this.y=s[1]*t+s[4]*n+s[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,t){return this.x=Be(this.x,e.x,t.x),this.y=Be(this.y,e.y,t.y),this}clampScalar(e,t){return this.x=Be(this.x,e,t),this.y=Be(this.y,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Be(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(Be(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y;return t*t+n*n}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this}rotateAround(e,t){let n=Math.cos(t),s=Math.sin(t),r=this.x-e.x,a=this.y-e.y;return this.x=r*n-a*s+e.x,this.y=r*s+a*n+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}},yn=class{constructor(e=0,t=0,n=0,s=1){this.isQuaternion=!0,this._x=e,this._y=t,this._z=n,this._w=s}static slerpFlat(e,t,n,s,r,a,o){let c=n[s+0],l=n[s+1],h=n[s+2],f=n[s+3],p=r[a+0],d=r[a+1],_=r[a+2],y=r[a+3];if(o<=0){e[t+0]=c,e[t+1]=l,e[t+2]=h,e[t+3]=f;return}if(o>=1){e[t+0]=p,e[t+1]=d,e[t+2]=_,e[t+3]=y;return}if(f!==y||c!==p||l!==d||h!==_){let m=c*p+l*d+h*_+f*y;m<0&&(p=-p,d=-d,_=-_,y=-y,m=-m);let u=1-o;if(m<.9995){let b=Math.acos(m),T=Math.sin(b);u=Math.sin(u*b)/T,o=Math.sin(o*b)/T,c=c*u+p*o,l=l*u+d*o,h=h*u+_*o,f=f*u+y*o}else{c=c*u+p*o,l=l*u+d*o,h=h*u+_*o,f=f*u+y*o;let b=1/Math.sqrt(c*c+l*l+h*h+f*f);c*=b,l*=b,h*=b,f*=b}}e[t]=c,e[t+1]=l,e[t+2]=h,e[t+3]=f}static multiplyQuaternionsFlat(e,t,n,s,r,a){let o=n[s],c=n[s+1],l=n[s+2],h=n[s+3],f=r[a],p=r[a+1],d=r[a+2],_=r[a+3];return e[t]=o*_+h*f+c*d-l*p,e[t+1]=c*_+h*p+l*f-o*d,e[t+2]=l*_+h*d+o*p-c*f,e[t+3]=h*_-o*f-c*p-l*d,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,t,n,s){return this._x=e,this._y=t,this._z=n,this._w=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,t=!0){let n=e._x,s=e._y,r=e._z,a=e._order,o=Math.cos,c=Math.sin,l=o(n/2),h=o(s/2),f=o(r/2),p=c(n/2),d=c(s/2),_=c(r/2);switch(a){case"XYZ":this._x=p*h*f+l*d*_,this._y=l*d*f-p*h*_,this._z=l*h*_+p*d*f,this._w=l*h*f-p*d*_;break;case"YXZ":this._x=p*h*f+l*d*_,this._y=l*d*f-p*h*_,this._z=l*h*_-p*d*f,this._w=l*h*f+p*d*_;break;case"ZXY":this._x=p*h*f-l*d*_,this._y=l*d*f+p*h*_,this._z=l*h*_+p*d*f,this._w=l*h*f-p*d*_;break;case"ZYX":this._x=p*h*f-l*d*_,this._y=l*d*f+p*h*_,this._z=l*h*_-p*d*f,this._w=l*h*f+p*d*_;break;case"YZX":this._x=p*h*f+l*d*_,this._y=l*d*f+p*h*_,this._z=l*h*_-p*d*f,this._w=l*h*f-p*d*_;break;case"XZY":this._x=p*h*f-l*d*_,this._y=l*d*f-p*h*_,this._z=l*h*_+p*d*f,this._w=l*h*f+p*d*_;break;default:Ce("Quaternion: .setFromEuler() encountered an unknown order: "+a)}return t===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,t){let n=t/2,s=Math.sin(n);return this._x=e.x*s,this._y=e.y*s,this._z=e.z*s,this._w=Math.cos(n),this._onChangeCallback(),this}setFromRotationMatrix(e){let t=e.elements,n=t[0],s=t[4],r=t[8],a=t[1],o=t[5],c=t[9],l=t[2],h=t[6],f=t[10],p=n+o+f;if(p>0){let d=.5/Math.sqrt(p+1);this._w=.25/d,this._x=(h-c)*d,this._y=(r-l)*d,this._z=(a-s)*d}else if(n>o&&n>f){let d=2*Math.sqrt(1+n-o-f);this._w=(h-c)/d,this._x=.25*d,this._y=(s+a)/d,this._z=(r+l)/d}else if(o>f){let d=2*Math.sqrt(1+o-n-f);this._w=(r-l)/d,this._x=(s+a)/d,this._y=.25*d,this._z=(c+h)/d}else{let d=2*Math.sqrt(1+f-n-o);this._w=(a-s)/d,this._x=(r+l)/d,this._y=(c+h)/d,this._z=.25*d}return this._onChangeCallback(),this}setFromUnitVectors(e,t){let n=e.dot(t)+1;return n<1e-8?(n=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=n):(this._x=0,this._y=-e.z,this._z=e.y,this._w=n)):(this._x=e.y*t.z-e.z*t.y,this._y=e.z*t.x-e.x*t.z,this._z=e.x*t.y-e.y*t.x,this._w=n),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(Be(this.dot(e),-1,1)))}rotateTowards(e,t){let n=this.angleTo(e);if(n===0)return this;let s=Math.min(1,t/n);return this.slerp(e,s),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,t){let n=e._x,s=e._y,r=e._z,a=e._w,o=t._x,c=t._y,l=t._z,h=t._w;return this._x=n*h+a*o+s*l-r*c,this._y=s*h+a*c+r*o-n*l,this._z=r*h+a*l+n*c-s*o,this._w=a*h-n*o-s*c-r*l,this._onChangeCallback(),this}slerp(e,t){if(t<=0)return this;if(t>=1)return this.copy(e);let n=e._x,s=e._y,r=e._z,a=e._w,o=this.dot(e);o<0&&(n=-n,s=-s,r=-r,a=-a,o=-o);let c=1-t;if(o<.9995){let l=Math.acos(o),h=Math.sin(l);c=Math.sin(c*l)/h,t=Math.sin(t*l)/h,this._x=this._x*c+n*t,this._y=this._y*c+s*t,this._z=this._z*c+r*t,this._w=this._w*c+a*t,this._onChangeCallback()}else this._x=this._x*c+n*t,this._y=this._y*c+s*t,this._z=this._z*c+r*t,this._w=this._w*c+a*t,this.normalize();return this}slerpQuaternions(e,t,n){return this.copy(e).slerp(t,n)}random(){let e=2*Math.PI*Math.random(),t=2*Math.PI*Math.random(),n=Math.random(),s=Math.sqrt(1-n),r=Math.sqrt(n);return this.set(s*Math.sin(e),s*Math.cos(e),r*Math.sin(t),r*Math.cos(t))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,t=0){return this._x=e[t],this._y=e[t+1],this._z=e[t+2],this._w=e[t+3],this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._w,e}fromBufferAttribute(e,t){return this._x=e.getX(t),this._y=e.getY(t),this._z=e.getZ(t),this._w=e.getW(t),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}},F=class i{constructor(e=0,t=0,n=0){i.prototype.isVector3=!0,this.x=e,this.y=t,this.z=n}set(e,t,n){return n===void 0&&(n=this.z),this.x=e,this.y=t,this.z=n,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,t){return this.x=e.x*t.x,this.y=e.y*t.y,this.z=e.z*t.z,this}applyEuler(e){return this.applyQuaternion(Fo.setFromEuler(e))}applyAxisAngle(e,t){return this.applyQuaternion(Fo.setFromAxisAngle(e,t))}applyMatrix3(e){let t=this.x,n=this.y,s=this.z,r=e.elements;return this.x=r[0]*t+r[3]*n+r[6]*s,this.y=r[1]*t+r[4]*n+r[7]*s,this.z=r[2]*t+r[5]*n+r[8]*s,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){let t=this.x,n=this.y,s=this.z,r=e.elements,a=1/(r[3]*t+r[7]*n+r[11]*s+r[15]);return this.x=(r[0]*t+r[4]*n+r[8]*s+r[12])*a,this.y=(r[1]*t+r[5]*n+r[9]*s+r[13])*a,this.z=(r[2]*t+r[6]*n+r[10]*s+r[14])*a,this}applyQuaternion(e){let t=this.x,n=this.y,s=this.z,r=e.x,a=e.y,o=e.z,c=e.w,l=2*(a*s-o*n),h=2*(o*t-r*s),f=2*(r*n-a*t);return this.x=t+c*l+a*f-o*h,this.y=n+c*h+o*l-r*f,this.z=s+c*f+r*h-a*l,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){let t=this.x,n=this.y,s=this.z,r=e.elements;return this.x=r[0]*t+r[4]*n+r[8]*s,this.y=r[1]*t+r[5]*n+r[9]*s,this.z=r[2]*t+r[6]*n+r[10]*s,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,t){return this.x=Be(this.x,e.x,t.x),this.y=Be(this.y,e.y,t.y),this.z=Be(this.z,e.z,t.z),this}clampScalar(e,t){return this.x=Be(this.x,e,t),this.y=Be(this.y,e,t),this.z=Be(this.z,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Be(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,t){let n=e.x,s=e.y,r=e.z,a=t.x,o=t.y,c=t.z;return this.x=s*c-r*o,this.y=r*a-n*c,this.z=n*o-s*a,this}projectOnVector(e){let t=e.lengthSq();if(t===0)return this.set(0,0,0);let n=e.dot(this)/t;return this.copy(e).multiplyScalar(n)}projectOnPlane(e){return ua.copy(this).projectOnVector(e),this.sub(ua)}reflect(e){return this.sub(ua.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(Be(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y,s=this.z-e.z;return t*t+n*n+s*s}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,t,n){let s=Math.sin(t)*e;return this.x=s*Math.sin(n),this.y=Math.cos(t)*e,this.z=s*Math.cos(n),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,t,n){return this.x=e*Math.sin(t),this.y=n,this.z=e*Math.cos(t),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this}setFromMatrixScale(e){let t=this.setFromMatrixColumn(e,0).length(),n=this.setFromMatrixColumn(e,1).length(),s=this.setFromMatrixColumn(e,2).length();return this.x=t,this.y=n,this.z=s,this}setFromMatrixColumn(e,t){return this.fromArray(e.elements,t*4)}setFromMatrix3Column(e,t){return this.fromArray(e.elements,t*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){let e=Math.random()*Math.PI*2,t=Math.random()*2-1,n=Math.sqrt(1-t*t);return this.x=n*Math.cos(e),this.y=t,this.z=n*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}},ua=new F,Fo=new yn,Ie=class i{constructor(e,t,n,s,r,a,o,c,l){i.prototype.isMatrix3=!0,this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,t,n,s,r,a,o,c,l)}set(e,t,n,s,r,a,o,c,l){let h=this.elements;return h[0]=e,h[1]=s,h[2]=o,h[3]=t,h[4]=r,h[5]=c,h[6]=n,h[7]=a,h[8]=l,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],this}extractBasis(e,t,n){return e.setFromMatrix3Column(this,0),t.setFromMatrix3Column(this,1),n.setFromMatrix3Column(this,2),this}setFromMatrix4(e){let t=e.elements;return this.set(t[0],t[4],t[8],t[1],t[5],t[9],t[2],t[6],t[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,s=t.elements,r=this.elements,a=n[0],o=n[3],c=n[6],l=n[1],h=n[4],f=n[7],p=n[2],d=n[5],_=n[8],y=s[0],m=s[3],u=s[6],b=s[1],T=s[4],A=s[7],E=s[2],w=s[5],I=s[8];return r[0]=a*y+o*b+c*E,r[3]=a*m+o*T+c*w,r[6]=a*u+o*A+c*I,r[1]=l*y+h*b+f*E,r[4]=l*m+h*T+f*w,r[7]=l*u+h*A+f*I,r[2]=p*y+d*b+_*E,r[5]=p*m+d*T+_*w,r[8]=p*u+d*A+_*I,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[3]*=e,t[6]*=e,t[1]*=e,t[4]*=e,t[7]*=e,t[2]*=e,t[5]*=e,t[8]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],c=e[6],l=e[7],h=e[8];return t*a*h-t*o*l-n*r*h+n*o*c+s*r*l-s*a*c}invert(){let e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],c=e[6],l=e[7],h=e[8],f=h*a-o*l,p=o*c-h*r,d=l*r-a*c,_=t*f+n*p+s*d;if(_===0)return this.set(0,0,0,0,0,0,0,0,0);let y=1/_;return e[0]=f*y,e[1]=(s*l-h*n)*y,e[2]=(o*n-s*a)*y,e[3]=p*y,e[4]=(h*t-s*c)*y,e[5]=(s*r-o*t)*y,e[6]=d*y,e[7]=(n*c-l*t)*y,e[8]=(a*t-n*r)*y,this}transpose(){let e,t=this.elements;return e=t[1],t[1]=t[3],t[3]=e,e=t[2],t[2]=t[6],t[6]=e,e=t[5],t[5]=t[7],t[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){let t=this.elements;return e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8],this}setUvTransform(e,t,n,s,r,a,o){let c=Math.cos(r),l=Math.sin(r);return this.set(n*c,n*l,-n*(c*a+l*o)+a+e,-s*l,s*c,-s*(-l*a+c*o)+o+t,0,0,1),this}scale(e,t){return this.premultiply(da.makeScale(e,t)),this}rotate(e){return this.premultiply(da.makeRotation(-e)),this}translate(e,t){return this.premultiply(da.makeTranslation(e,t)),this}makeTranslation(e,t){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,t,0,0,1),this}makeRotation(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,n,t,0,0,0,1),this}makeScale(e,t){return this.set(e,0,0,0,t,0,0,0,1),this}equals(e){let t=this.elements,n=e.elements;for(let s=0;s<9;s++)if(t[s]!==n[s])return!1;return!0}fromArray(e,t=0){for(let n=0;n<9;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e}clone(){return new this.constructor().fromArray(this.elements)}},da=new Ie,Oo=new Ie().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),Bo=new Ie().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function vc(){let i={enabled:!0,workingColorSpace:Zn,spaces:{},convert:function(s,r,a){return this.enabled===!1||r===a||!r||!a||(this.spaces[r].transfer===Xe&&(s.r=_n(s.r),s.g=_n(s.g),s.b=_n(s.b)),this.spaces[r].primaries!==this.spaces[a].primaries&&(s.applyMatrix3(this.spaces[r].toXYZ),s.applyMatrix3(this.spaces[a].fromXYZ)),this.spaces[a].transfer===Xe&&(s.r=xi(s.r),s.g=xi(s.g),s.b=xi(s.b))),s},workingToColorSpace:function(s,r){return this.convert(s,this.workingColorSpace,r)},colorSpaceToWorking:function(s,r){return this.convert(s,r,this.workingColorSpace)},getPrimaries:function(s){return this.spaces[s].primaries},getTransfer:function(s){return s===Mn?Bi:this.spaces[s].transfer},getToneMappingMode:function(s){return this.spaces[s].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(s,r=this.workingColorSpace){return s.fromArray(this.spaces[r].luminanceCoefficients)},define:function(s){Object.assign(this.spaces,s)},_getMatrix:function(s,r,a){return s.copy(this.spaces[r].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(s){return this.spaces[s].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(s=this.workingColorSpace){return this.spaces[s].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(s,r){return yi("ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),i.workingToColorSpace(s,r)},toWorkingColorSpace:function(s,r){return yi("ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),i.colorSpaceToWorking(s,r)}},e=[.64,.33,.3,.6,.15,.06],t=[.2126,.7152,.0722],n=[.3127,.329];return i.define({[Zn]:{primaries:e,whitePoint:n,transfer:Bi,toXYZ:Oo,fromXYZ:Bo,luminanceCoefficients:t,workingColorSpaceConfig:{unpackColorSpace:bt},outputColorSpaceConfig:{drawingBufferColorSpace:bt}},[bt]:{primaries:e,whitePoint:n,transfer:Xe,toXYZ:Oo,fromXYZ:Bo,luminanceCoefficients:t,outputColorSpaceConfig:{drawingBufferColorSpace:bt}}}),i}var ze=vc();function _n(i){return i<.04045?i*.0773993808:Math.pow(i*.9478672986+.0521327014,2.4)}function xi(i){return i<.0031308?i*12.92:1.055*Math.pow(i,.41666)-.055}var ai,Bs=class{static getDataURL(e,t="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let n;if(e instanceof HTMLCanvasElement)n=e;else{ai===void 0&&(ai=Vi("canvas")),ai.width=e.width,ai.height=e.height;let s=ai.getContext("2d");e instanceof ImageData?s.putImageData(e,0,0):s.drawImage(e,0,0,e.width,e.height),n=ai}return n.toDataURL(t)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){let t=Vi("canvas");t.width=e.width,t.height=e.height;let n=t.getContext("2d");n.drawImage(e,0,0,e.width,e.height);let s=n.getImageData(0,0,e.width,e.height),r=s.data;for(let a=0;a<r.length;a++)r[a]=_n(r[a]/255)*255;return n.putImageData(s,0,0),t}else if(e.data){let t=e.data.slice(0);for(let n=0;n<t.length;n++)t instanceof Uint8Array||t instanceof Uint8ClampedArray?t[n]=Math.floor(_n(t[n]/255)*255):t[n]=_n(t[n]);return{data:t,width:e.width,height:e.height}}else return Ce("ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}},yc=0,Mi=class{constructor(e=null){this.isSource=!0,Object.defineProperty(this,"id",{value:yc++}),this.uuid=os(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){let t=this.data;return typeof HTMLVideoElement<"u"&&t instanceof HTMLVideoElement?e.set(t.videoWidth,t.videoHeight,0):typeof VideoFrame<"u"&&t instanceof VideoFrame?e.set(t.displayHeight,t.displayWidth,0):t!==null?e.set(t.width,t.height,t.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){let t=e===void 0||typeof e=="string";if(!t&&e.images[this.uuid]!==void 0)return e.images[this.uuid];let n={uuid:this.uuid,url:""},s=this.data;if(s!==null){let r;if(Array.isArray(s)){r=[];for(let a=0,o=s.length;a<o;a++)s[a].isDataTexture?r.push(fa(s[a].image)):r.push(fa(s[a]))}else r=fa(s);n.url=r}return t||(e.images[this.uuid]=n),n}};function fa(i){return typeof HTMLImageElement<"u"&&i instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&i instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&i instanceof ImageBitmap?Bs.getDataURL(i):i.data?{data:Array.from(i.data),width:i.width,height:i.height,type:i.data.constructor.name}:(Ce("Texture: Unable to serialize Texture."),{})}var Mc=0,pa=new F,At=class i extends vn{constructor(e=i.DEFAULT_IMAGE,t=i.DEFAULT_MAPPING,n=en,s=en,r=_t,a=Fn,o=Ht,c=Bt,l=i.DEFAULT_ANISOTROPY,h=Mn){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:Mc++}),this.uuid=os(),this.name="",this.source=new Mi(e),this.mipmaps=[],this.mapping=t,this.channel=0,this.wrapS=n,this.wrapT=s,this.magFilter=r,this.minFilter=a,this.anisotropy=l,this.format=o,this.internalFormat=null,this.type=c,this.offset=new Je(0,0),this.repeat=new Je(1,1),this.center=new Je(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new Ie,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=h,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0}get width(){return this.source.getSize(pa).x}get height(){return this.source.getSize(pa).y}get depth(){return this.source.getSize(pa).z}get image(){return this.source.data}set image(e=null){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(let t in e){let n=e[t];if(n===void 0){Ce(`Texture.setValues(): parameter '${t}' has value of undefined.`);continue}let s=this[t];if(s===void 0){Ce(`Texture.setValues(): property '${t}' does not exist.`);continue}s&&n&&s.isVector2&&n.isVector2||s&&n&&s.isVector3&&n.isVector3||s&&n&&s.isMatrix3&&n.isMatrix3?s.copy(n):this[t]=n}}toJSON(e){let t=e===void 0||typeof e=="string";if(!t&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];let n={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(n.userData=this.userData),t||(e.textures[this.uuid]=n),n}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==$a)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case Us:e.x=e.x-Math.floor(e.x);break;case en:e.x=e.x<0?0:1;break;case Ns:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case Us:e.y=e.y-Math.floor(e.y);break;case en:e.y=e.y<0?0:1;break;case Ns:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}};At.DEFAULT_IMAGE=null;At.DEFAULT_MAPPING=$a;At.DEFAULT_ANISOTROPY=1;var ot=class i{constructor(e=0,t=0,n=0,s=1){i.prototype.isVector4=!0,this.x=e,this.y=t,this.z=n,this.w=s}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,t,n,s){return this.x=e,this.y=t,this.z=n,this.w=s,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;case 3:this.w=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this.w=e.w+t.w,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this.w+=e.w*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this.w=e.w-t.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){let t=this.x,n=this.y,s=this.z,r=this.w,a=e.elements;return this.x=a[0]*t+a[4]*n+a[8]*s+a[12]*r,this.y=a[1]*t+a[5]*n+a[9]*s+a[13]*r,this.z=a[2]*t+a[6]*n+a[10]*s+a[14]*r,this.w=a[3]*t+a[7]*n+a[11]*s+a[15]*r,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);let t=Math.sqrt(1-e.w*e.w);return t<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/t,this.y=e.y/t,this.z=e.z/t),this}setAxisAngleFromRotationMatrix(e){let t,n,s,r,c=e.elements,l=c[0],h=c[4],f=c[8],p=c[1],d=c[5],_=c[9],y=c[2],m=c[6],u=c[10];if(Math.abs(h-p)<.01&&Math.abs(f-y)<.01&&Math.abs(_-m)<.01){if(Math.abs(h+p)<.1&&Math.abs(f+y)<.1&&Math.abs(_+m)<.1&&Math.abs(l+d+u-3)<.1)return this.set(1,0,0,0),this;t=Math.PI;let T=(l+1)/2,A=(d+1)/2,E=(u+1)/2,w=(h+p)/4,I=(f+y)/4,B=(_+m)/4;return T>A&&T>E?T<.01?(n=0,s=.707106781,r=.707106781):(n=Math.sqrt(T),s=w/n,r=I/n):A>E?A<.01?(n=.707106781,s=0,r=.707106781):(s=Math.sqrt(A),n=w/s,r=B/s):E<.01?(n=.707106781,s=.707106781,r=0):(r=Math.sqrt(E),n=I/r,s=B/r),this.set(n,s,r,t),this}let b=Math.sqrt((m-_)*(m-_)+(f-y)*(f-y)+(p-h)*(p-h));return Math.abs(b)<.001&&(b=1),this.x=(m-_)/b,this.y=(f-y)/b,this.z=(p-h)/b,this.w=Math.acos((l+d+u-1)/2),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this.w=t[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,t){return this.x=Be(this.x,e.x,t.x),this.y=Be(this.y,e.y,t.y),this.z=Be(this.z,e.z,t.z),this.w=Be(this.w,e.w,t.w),this}clampScalar(e,t){return this.x=Be(this.x,e,t),this.y=Be(this.y,e,t),this.z=Be(this.z,e,t),this.w=Be(this.w,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Be(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this.w+=(e.w-this.w)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this.w=e.w+(t.w-e.w)*n,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this.w=e[t+3],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e[t+3]=this.w,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this.w=e.getW(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}},zs=class extends vn{constructor(e=1,t=1,n={}){super(),n=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:_t,depthBuffer:!0,stencilBuffer:!1,resolveDepthBuffer:!0,resolveStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1},n),this.isRenderTarget=!0,this.width=e,this.height=t,this.depth=n.depth,this.scissor=new ot(0,0,e,t),this.scissorTest=!1,this.viewport=new ot(0,0,e,t);let s={width:e,height:t,depth:n.depth},r=new At(s);this.textures=[];let a=n.count;for(let o=0;o<a;o++)this.textures[o]=r.clone(),this.textures[o].isRenderTargetTexture=!0,this.textures[o].renderTarget=this;this._setTextureOptions(n),this.depthBuffer=n.depthBuffer,this.stencilBuffer=n.stencilBuffer,this.resolveDepthBuffer=n.resolveDepthBuffer,this.resolveStencilBuffer=n.resolveStencilBuffer,this._depthTexture=null,this.depthTexture=n.depthTexture,this.samples=n.samples,this.multiview=n.multiview}_setTextureOptions(e={}){let t={minFilter:_t,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(t.mapping=e.mapping),e.wrapS!==void 0&&(t.wrapS=e.wrapS),e.wrapT!==void 0&&(t.wrapT=e.wrapT),e.wrapR!==void 0&&(t.wrapR=e.wrapR),e.magFilter!==void 0&&(t.magFilter=e.magFilter),e.minFilter!==void 0&&(t.minFilter=e.minFilter),e.format!==void 0&&(t.format=e.format),e.type!==void 0&&(t.type=e.type),e.anisotropy!==void 0&&(t.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(t.colorSpace=e.colorSpace),e.flipY!==void 0&&(t.flipY=e.flipY),e.generateMipmaps!==void 0&&(t.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(t.internalFormat=e.internalFormat);for(let n=0;n<this.textures.length;n++)this.textures[n].setValues(t)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&(this._depthTexture.renderTarget=null),e!==null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,t,n=1){if(this.width!==e||this.height!==t||this.depth!==n){this.width=e,this.height=t,this.depth=n;for(let s=0,r=this.textures.length;s<r;s++)this.textures[s].image.width=e,this.textures[s].image.height=t,this.textures[s].image.depth=n,this.textures[s].isData3DTexture!==!0&&(this.textures[s].isArrayTexture=this.textures[s].image.depth>1);this.dispose()}this.viewport.set(0,0,e,t),this.scissor.set(0,0,e,t)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let t=0,n=e.textures.length;t<n;t++){this.textures[t]=e.textures[t].clone(),this.textures[t].isRenderTargetTexture=!0,this.textures[t].renderTarget=this;let s=Object.assign({},e.textures[t].image);this.textures[t].source=new Mi(s)}return this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,e.depthTexture!==null&&(this.depthTexture=e.depthTexture.clone()),this.samples=e.samples,this}dispose(){this.dispatchEvent({type:"dispose"})}},Nt=class extends zs{constructor(e=1,t=1,n={}){super(e,t,n),this.isWebGLRenderTarget=!0}},ki=class extends At{constructor(e=null,t=1,n=1,s=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:t,height:n,depth:s},this.magFilter=gt,this.minFilter=gt,this.wrapR=en,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}};var Vs=class extends At{constructor(e=null,t=1,n=1,s=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:t,height:n,depth:s},this.magFilter=gt,this.minFilter=gt,this.wrapR=en,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}};var Pn=class{constructor(e=new F(1/0,1/0,1/0),t=new F(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=t}set(e,t){return this.min.copy(e),this.max.copy(t),this}setFromArray(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t+=3)this.expandByPoint(Xt.fromArray(e,t));return this}setFromBufferAttribute(e){this.makeEmpty();for(let t=0,n=e.count;t<n;t++)this.expandByPoint(Xt.fromBufferAttribute(e,t));return this}setFromPoints(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t++)this.expandByPoint(e[t]);return this}setFromCenterAndSize(e,t){let n=Xt.copy(t).multiplyScalar(.5);return this.min.copy(e).sub(n),this.max.copy(e).add(n),this}setFromObject(e,t=!1){return this.makeEmpty(),this.expandByObject(e,t)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,t=!1){e.updateWorldMatrix(!1,!1);let n=e.geometry;if(n!==void 0){let r=n.getAttribute("position");if(t===!0&&r!==void 0&&e.isInstancedMesh!==!0)for(let a=0,o=r.count;a<o;a++)e.isMesh===!0?e.getVertexPosition(a,Xt):Xt.fromBufferAttribute(r,a),Xt.applyMatrix4(e.matrixWorld),this.expandByPoint(Xt);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),fs.copy(e.boundingBox)):(n.boundingBox===null&&n.computeBoundingBox(),fs.copy(n.boundingBox)),fs.applyMatrix4(e.matrixWorld),this.union(fs)}let s=e.children;for(let r=0,a=s.length;r<a;r++)this.expandByObject(s[r],t);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,t){return t.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,Xt),Xt.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let t,n;return e.normal.x>0?(t=e.normal.x*this.min.x,n=e.normal.x*this.max.x):(t=e.normal.x*this.max.x,n=e.normal.x*this.min.x),e.normal.y>0?(t+=e.normal.y*this.min.y,n+=e.normal.y*this.max.y):(t+=e.normal.y*this.max.y,n+=e.normal.y*this.min.y),e.normal.z>0?(t+=e.normal.z*this.min.z,n+=e.normal.z*this.max.z):(t+=e.normal.z*this.max.z,n+=e.normal.z*this.min.z),t<=-e.constant&&n>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(Di),ps.subVectors(this.max,Di),oi.subVectors(e.a,Di),li.subVectors(e.b,Di),ci.subVectors(e.c,Di),bn.subVectors(li,oi),An.subVectors(ci,li),kn.subVectors(oi,ci);let t=[0,-bn.z,bn.y,0,-An.z,An.y,0,-kn.z,kn.y,bn.z,0,-bn.x,An.z,0,-An.x,kn.z,0,-kn.x,-bn.y,bn.x,0,-An.y,An.x,0,-kn.y,kn.x,0];return!ma(t,oi,li,ci,ps)||(t=[1,0,0,0,1,0,0,0,1],!ma(t,oi,li,ci,ps))?!1:(ms.crossVectors(bn,An),t=[ms.x,ms.y,ms.z],ma(t,oi,li,ci,ps))}clampPoint(e,t){return t.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,Xt).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(Xt).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(un[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),un[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),un[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),un[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),un[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),un[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),un[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),un[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(un),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}},un=[new F,new F,new F,new F,new F,new F,new F,new F],Xt=new F,fs=new Pn,oi=new F,li=new F,ci=new F,bn=new F,An=new F,kn=new F,Di=new F,ps=new F,ms=new F,Gn=new F;function ma(i,e,t,n,s){for(let r=0,a=i.length-3;r<=a;r+=3){Gn.fromArray(i,r);let o=s.x*Math.abs(Gn.x)+s.y*Math.abs(Gn.y)+s.z*Math.abs(Gn.z),c=e.dot(Gn),l=t.dot(Gn),h=n.dot(Gn);if(Math.max(-Math.max(c,l,h),Math.min(c,l,h))>o)return!1}return!0}var Sc=new Pn,Ui=new F,ga=new F,Si=class{constructor(e=new F,t=-1){this.isSphere=!0,this.center=e,this.radius=t}set(e,t){return this.center.copy(e),this.radius=t,this}setFromPoints(e,t){let n=this.center;t!==void 0?n.copy(t):Sc.setFromPoints(e).getCenter(n);let s=0;for(let r=0,a=e.length;r<a;r++)s=Math.max(s,n.distanceToSquared(e[r]));return this.radius=Math.sqrt(s),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){let t=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=t*t}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,t){let n=this.center.distanceToSquared(e);return t.copy(e),n>this.radius*this.radius&&(t.sub(this.center).normalize(),t.multiplyScalar(this.radius).add(this.center)),t}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;Ui.subVectors(e,this.center);let t=Ui.lengthSq();if(t>this.radius*this.radius){let n=Math.sqrt(t),s=(n-this.radius)*.5;this.center.addScaledVector(Ui,s/n),this.radius+=s}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(ga.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint(Ui.copy(e.center).add(ga)),this.expandByPoint(Ui.copy(e.center).sub(ga))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}},dn=new F,_a=new F,gs=new F,Tn=new F,xa=new F,_s=new F,va=new F,ks=class{constructor(e=new F,t=new F(0,0,-1)){this.origin=e,this.direction=t}set(e,t){return this.origin.copy(e),this.direction.copy(t),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,t){return t.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,dn)),this}closestPointToPoint(e,t){t.subVectors(e,this.origin);let n=t.dot(this.direction);return n<0?t.copy(this.origin):t.copy(this.origin).addScaledVector(this.direction,n)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){let t=dn.subVectors(e,this.origin).dot(this.direction);return t<0?this.origin.distanceToSquared(e):(dn.copy(this.origin).addScaledVector(this.direction,t),dn.distanceToSquared(e))}distanceSqToSegment(e,t,n,s){_a.copy(e).add(t).multiplyScalar(.5),gs.copy(t).sub(e).normalize(),Tn.copy(this.origin).sub(_a);let r=e.distanceTo(t)*.5,a=-this.direction.dot(gs),o=Tn.dot(this.direction),c=-Tn.dot(gs),l=Tn.lengthSq(),h=Math.abs(1-a*a),f,p,d,_;if(h>0)if(f=a*c-o,p=a*o-c,_=r*h,f>=0)if(p>=-_)if(p<=_){let y=1/h;f*=y,p*=y,d=f*(f+a*p+2*o)+p*(a*f+p+2*c)+l}else p=r,f=Math.max(0,-(a*p+o)),d=-f*f+p*(p+2*c)+l;else p=-r,f=Math.max(0,-(a*p+o)),d=-f*f+p*(p+2*c)+l;else p<=-_?(f=Math.max(0,-(-a*r+o)),p=f>0?-r:Math.min(Math.max(-r,-c),r),d=-f*f+p*(p+2*c)+l):p<=_?(f=0,p=Math.min(Math.max(-r,-c),r),d=p*(p+2*c)+l):(f=Math.max(0,-(a*r+o)),p=f>0?r:Math.min(Math.max(-r,-c),r),d=-f*f+p*(p+2*c)+l);else p=a>0?-r:r,f=Math.max(0,-(a*p+o)),d=-f*f+p*(p+2*c)+l;return n&&n.copy(this.origin).addScaledVector(this.direction,f),s&&s.copy(_a).addScaledVector(gs,p),d}intersectSphere(e,t){dn.subVectors(e.center,this.origin);let n=dn.dot(this.direction),s=dn.dot(dn)-n*n,r=e.radius*e.radius;if(s>r)return null;let a=Math.sqrt(r-s),o=n-a,c=n+a;return c<0?null:o<0?this.at(c,t):this.at(o,t)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){let t=e.normal.dot(this.direction);if(t===0)return e.distanceToPoint(this.origin)===0?0:null;let n=-(this.origin.dot(e.normal)+e.constant)/t;return n>=0?n:null}intersectPlane(e,t){let n=this.distanceToPlane(e);return n===null?null:this.at(n,t)}intersectsPlane(e){let t=e.distanceToPoint(this.origin);return t===0||e.normal.dot(this.direction)*t<0}intersectBox(e,t){let n,s,r,a,o,c,l=1/this.direction.x,h=1/this.direction.y,f=1/this.direction.z,p=this.origin;return l>=0?(n=(e.min.x-p.x)*l,s=(e.max.x-p.x)*l):(n=(e.max.x-p.x)*l,s=(e.min.x-p.x)*l),h>=0?(r=(e.min.y-p.y)*h,a=(e.max.y-p.y)*h):(r=(e.max.y-p.y)*h,a=(e.min.y-p.y)*h),n>a||r>s||((r>n||isNaN(n))&&(n=r),(a<s||isNaN(s))&&(s=a),f>=0?(o=(e.min.z-p.z)*f,c=(e.max.z-p.z)*f):(o=(e.max.z-p.z)*f,c=(e.min.z-p.z)*f),n>c||o>s)||((o>n||n!==n)&&(n=o),(c<s||s!==s)&&(s=c),s<0)?null:this.at(n>=0?n:s,t)}intersectsBox(e){return this.intersectBox(e,dn)!==null}intersectTriangle(e,t,n,s,r){xa.subVectors(t,e),_s.subVectors(n,e),va.crossVectors(xa,_s);let a=this.direction.dot(va),o;if(a>0){if(s)return null;o=1}else if(a<0)o=-1,a=-a;else return null;Tn.subVectors(this.origin,e);let c=o*this.direction.dot(_s.crossVectors(Tn,_s));if(c<0)return null;let l=o*this.direction.dot(xa.cross(Tn));if(l<0||c+l>a)return null;let h=-o*Tn.dot(va);return h<0?null:this.at(h/a,r)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}},ut=class i{constructor(e,t,n,s,r,a,o,c,l,h,f,p,d,_,y,m){i.prototype.isMatrix4=!0,this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,t,n,s,r,a,o,c,l,h,f,p,d,_,y,m)}set(e,t,n,s,r,a,o,c,l,h,f,p,d,_,y,m){let u=this.elements;return u[0]=e,u[4]=t,u[8]=n,u[12]=s,u[1]=r,u[5]=a,u[9]=o,u[13]=c,u[2]=l,u[6]=h,u[10]=f,u[14]=p,u[3]=d,u[7]=_,u[11]=y,u[15]=m,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new i().fromArray(this.elements)}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],t[9]=n[9],t[10]=n[10],t[11]=n[11],t[12]=n[12],t[13]=n[13],t[14]=n[14],t[15]=n[15],this}copyPosition(e){let t=this.elements,n=e.elements;return t[12]=n[12],t[13]=n[13],t[14]=n[14],this}setFromMatrix3(e){let t=e.elements;return this.set(t[0],t[3],t[6],0,t[1],t[4],t[7],0,t[2],t[5],t[8],0,0,0,0,1),this}extractBasis(e,t,n){return this.determinant()===0?(e.set(1,0,0),t.set(0,1,0),n.set(0,0,1),this):(e.setFromMatrixColumn(this,0),t.setFromMatrixColumn(this,1),n.setFromMatrixColumn(this,2),this)}makeBasis(e,t,n){return this.set(e.x,t.x,n.x,0,e.y,t.y,n.y,0,e.z,t.z,n.z,0,0,0,0,1),this}extractRotation(e){if(e.determinant()===0)return this.identity();let t=this.elements,n=e.elements,s=1/hi.setFromMatrixColumn(e,0).length(),r=1/hi.setFromMatrixColumn(e,1).length(),a=1/hi.setFromMatrixColumn(e,2).length();return t[0]=n[0]*s,t[1]=n[1]*s,t[2]=n[2]*s,t[3]=0,t[4]=n[4]*r,t[5]=n[5]*r,t[6]=n[6]*r,t[7]=0,t[8]=n[8]*a,t[9]=n[9]*a,t[10]=n[10]*a,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromEuler(e){let t=this.elements,n=e.x,s=e.y,r=e.z,a=Math.cos(n),o=Math.sin(n),c=Math.cos(s),l=Math.sin(s),h=Math.cos(r),f=Math.sin(r);if(e.order==="XYZ"){let p=a*h,d=a*f,_=o*h,y=o*f;t[0]=c*h,t[4]=-c*f,t[8]=l,t[1]=d+_*l,t[5]=p-y*l,t[9]=-o*c,t[2]=y-p*l,t[6]=_+d*l,t[10]=a*c}else if(e.order==="YXZ"){let p=c*h,d=c*f,_=l*h,y=l*f;t[0]=p+y*o,t[4]=_*o-d,t[8]=a*l,t[1]=a*f,t[5]=a*h,t[9]=-o,t[2]=d*o-_,t[6]=y+p*o,t[10]=a*c}else if(e.order==="ZXY"){let p=c*h,d=c*f,_=l*h,y=l*f;t[0]=p-y*o,t[4]=-a*f,t[8]=_+d*o,t[1]=d+_*o,t[5]=a*h,t[9]=y-p*o,t[2]=-a*l,t[6]=o,t[10]=a*c}else if(e.order==="ZYX"){let p=a*h,d=a*f,_=o*h,y=o*f;t[0]=c*h,t[4]=_*l-d,t[8]=p*l+y,t[1]=c*f,t[5]=y*l+p,t[9]=d*l-_,t[2]=-l,t[6]=o*c,t[10]=a*c}else if(e.order==="YZX"){let p=a*c,d=a*l,_=o*c,y=o*l;t[0]=c*h,t[4]=y-p*f,t[8]=_*f+d,t[1]=f,t[5]=a*h,t[9]=-o*h,t[2]=-l*h,t[6]=d*f+_,t[10]=p-y*f}else if(e.order==="XZY"){let p=a*c,d=a*l,_=o*c,y=o*l;t[0]=c*h,t[4]=-f,t[8]=l*h,t[1]=p*f+y,t[5]=a*h,t[9]=d*f-_,t[2]=_*f-d,t[6]=o*h,t[10]=y*f+p}return t[3]=0,t[7]=0,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromQuaternion(e){return this.compose(bc,e,Ac)}lookAt(e,t,n){let s=this.elements;return Lt.subVectors(e,t),Lt.lengthSq()===0&&(Lt.z=1),Lt.normalize(),En.crossVectors(n,Lt),En.lengthSq()===0&&(Math.abs(n.z)===1?Lt.x+=1e-4:Lt.z+=1e-4,Lt.normalize(),En.crossVectors(n,Lt)),En.normalize(),xs.crossVectors(Lt,En),s[0]=En.x,s[4]=xs.x,s[8]=Lt.x,s[1]=En.y,s[5]=xs.y,s[9]=Lt.y,s[2]=En.z,s[6]=xs.z,s[10]=Lt.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,s=t.elements,r=this.elements,a=n[0],o=n[4],c=n[8],l=n[12],h=n[1],f=n[5],p=n[9],d=n[13],_=n[2],y=n[6],m=n[10],u=n[14],b=n[3],T=n[7],A=n[11],E=n[15],w=s[0],I=s[4],B=s[8],v=s[12],M=s[1],L=s[5],V=s[9],z=s[13],W=s[2],Y=s[6],k=s[10],H=s[14],$=s[3],he=s[7],ae=s[11],ue=s[15];return r[0]=a*w+o*M+c*W+l*$,r[4]=a*I+o*L+c*Y+l*he,r[8]=a*B+o*V+c*k+l*ae,r[12]=a*v+o*z+c*H+l*ue,r[1]=h*w+f*M+p*W+d*$,r[5]=h*I+f*L+p*Y+d*he,r[9]=h*B+f*V+p*k+d*ae,r[13]=h*v+f*z+p*H+d*ue,r[2]=_*w+y*M+m*W+u*$,r[6]=_*I+y*L+m*Y+u*he,r[10]=_*B+y*V+m*k+u*ae,r[14]=_*v+y*z+m*H+u*ue,r[3]=b*w+T*M+A*W+E*$,r[7]=b*I+T*L+A*Y+E*he,r[11]=b*B+T*V+A*k+E*ae,r[15]=b*v+T*z+A*H+E*ue,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[4]*=e,t[8]*=e,t[12]*=e,t[1]*=e,t[5]*=e,t[9]*=e,t[13]*=e,t[2]*=e,t[6]*=e,t[10]*=e,t[14]*=e,t[3]*=e,t[7]*=e,t[11]*=e,t[15]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[4],s=e[8],r=e[12],a=e[1],o=e[5],c=e[9],l=e[13],h=e[2],f=e[6],p=e[10],d=e[14],_=e[3],y=e[7],m=e[11],u=e[15],b=c*d-l*p,T=o*d-l*f,A=o*p-c*f,E=a*d-l*h,w=a*p-c*h,I=a*f-o*h;return t*(y*b-m*T+u*A)-n*(_*b-m*E+u*w)+s*(_*T-y*E+u*I)-r*(_*A-y*w+m*I)}transpose(){let e=this.elements,t;return t=e[1],e[1]=e[4],e[4]=t,t=e[2],e[2]=e[8],e[8]=t,t=e[6],e[6]=e[9],e[9]=t,t=e[3],e[3]=e[12],e[12]=t,t=e[7],e[7]=e[13],e[13]=t,t=e[11],e[11]=e[14],e[14]=t,this}setPosition(e,t,n){let s=this.elements;return e.isVector3?(s[12]=e.x,s[13]=e.y,s[14]=e.z):(s[12]=e,s[13]=t,s[14]=n),this}invert(){let e=this.elements,t=e[0],n=e[1],s=e[2],r=e[3],a=e[4],o=e[5],c=e[6],l=e[7],h=e[8],f=e[9],p=e[10],d=e[11],_=e[12],y=e[13],m=e[14],u=e[15],b=f*m*l-y*p*l+y*c*d-o*m*d-f*c*u+o*p*u,T=_*p*l-h*m*l-_*c*d+a*m*d+h*c*u-a*p*u,A=h*y*l-_*f*l+_*o*d-a*y*d-h*o*u+a*f*u,E=_*f*c-h*y*c-_*o*p+a*y*p+h*o*m-a*f*m,w=t*b+n*T+s*A+r*E;if(w===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);let I=1/w;return e[0]=b*I,e[1]=(y*p*r-f*m*r-y*s*d+n*m*d+f*s*u-n*p*u)*I,e[2]=(o*m*r-y*c*r+y*s*l-n*m*l-o*s*u+n*c*u)*I,e[3]=(f*c*r-o*p*r-f*s*l+n*p*l+o*s*d-n*c*d)*I,e[4]=T*I,e[5]=(h*m*r-_*p*r+_*s*d-t*m*d-h*s*u+t*p*u)*I,e[6]=(_*c*r-a*m*r-_*s*l+t*m*l+a*s*u-t*c*u)*I,e[7]=(a*p*r-h*c*r+h*s*l-t*p*l-a*s*d+t*c*d)*I,e[8]=A*I,e[9]=(_*f*r-h*y*r-_*n*d+t*y*d+h*n*u-t*f*u)*I,e[10]=(a*y*r-_*o*r+_*n*l-t*y*l-a*n*u+t*o*u)*I,e[11]=(h*o*r-a*f*r-h*n*l+t*f*l+a*n*d-t*o*d)*I,e[12]=E*I,e[13]=(h*y*s-_*f*s+_*n*p-t*y*p-h*n*m+t*f*m)*I,e[14]=(_*o*s-a*y*s-_*n*c+t*y*c+a*n*m-t*o*m)*I,e[15]=(a*f*s-h*o*s+h*n*c-t*f*c-a*n*p+t*o*p)*I,this}scale(e){let t=this.elements,n=e.x,s=e.y,r=e.z;return t[0]*=n,t[4]*=s,t[8]*=r,t[1]*=n,t[5]*=s,t[9]*=r,t[2]*=n,t[6]*=s,t[10]*=r,t[3]*=n,t[7]*=s,t[11]*=r,this}getMaxScaleOnAxis(){let e=this.elements,t=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],n=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],s=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(t,n,s))}makeTranslation(e,t,n){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,t,0,0,1,n,0,0,0,1),this}makeRotationX(e){let t=Math.cos(e),n=Math.sin(e);return this.set(1,0,0,0,0,t,-n,0,0,n,t,0,0,0,0,1),this}makeRotationY(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,0,n,0,0,1,0,0,-n,0,t,0,0,0,0,1),this}makeRotationZ(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,0,n,t,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,t){let n=Math.cos(t),s=Math.sin(t),r=1-n,a=e.x,o=e.y,c=e.z,l=r*a,h=r*o;return this.set(l*a+n,l*o-s*c,l*c+s*o,0,l*o+s*c,h*o+n,h*c-s*a,0,l*c-s*o,h*c+s*a,r*c*c+n,0,0,0,0,1),this}makeScale(e,t,n){return this.set(e,0,0,0,0,t,0,0,0,0,n,0,0,0,0,1),this}makeShear(e,t,n,s,r,a){return this.set(1,n,r,0,e,1,a,0,t,s,1,0,0,0,0,1),this}compose(e,t,n){let s=this.elements,r=t._x,a=t._y,o=t._z,c=t._w,l=r+r,h=a+a,f=o+o,p=r*l,d=r*h,_=r*f,y=a*h,m=a*f,u=o*f,b=c*l,T=c*h,A=c*f,E=n.x,w=n.y,I=n.z;return s[0]=(1-(y+u))*E,s[1]=(d+A)*E,s[2]=(_-T)*E,s[3]=0,s[4]=(d-A)*w,s[5]=(1-(p+u))*w,s[6]=(m+b)*w,s[7]=0,s[8]=(_+T)*I,s[9]=(m-b)*I,s[10]=(1-(p+y))*I,s[11]=0,s[12]=e.x,s[13]=e.y,s[14]=e.z,s[15]=1,this}decompose(e,t,n){let s=this.elements;if(e.x=s[12],e.y=s[13],e.z=s[14],this.determinant()===0)return n.set(1,1,1),t.identity(),this;let r=hi.set(s[0],s[1],s[2]).length(),a=hi.set(s[4],s[5],s[6]).length(),o=hi.set(s[8],s[9],s[10]).length();this.determinant()<0&&(r=-r),qt.copy(this);let l=1/r,h=1/a,f=1/o;return qt.elements[0]*=l,qt.elements[1]*=l,qt.elements[2]*=l,qt.elements[4]*=h,qt.elements[5]*=h,qt.elements[6]*=h,qt.elements[8]*=f,qt.elements[9]*=f,qt.elements[10]*=f,t.setFromRotationMatrix(qt),n.x=r,n.y=a,n.z=o,this}makePerspective(e,t,n,s,r,a,o=Zt,c=!1){let l=this.elements,h=2*r/(t-e),f=2*r/(n-s),p=(t+e)/(t-e),d=(n+s)/(n-s),_,y;if(c)_=r/(a-r),y=a*r/(a-r);else if(o===Zt)_=-(a+r)/(a-r),y=-2*a*r/(a-r);else if(o===zi)_=-a/(a-r),y=-a*r/(a-r);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+o);return l[0]=h,l[4]=0,l[8]=p,l[12]=0,l[1]=0,l[5]=f,l[9]=d,l[13]=0,l[2]=0,l[6]=0,l[10]=_,l[14]=y,l[3]=0,l[7]=0,l[11]=-1,l[15]=0,this}makeOrthographic(e,t,n,s,r,a,o=Zt,c=!1){let l=this.elements,h=2/(t-e),f=2/(n-s),p=-(t+e)/(t-e),d=-(n+s)/(n-s),_,y;if(c)_=1/(a-r),y=a/(a-r);else if(o===Zt)_=-2/(a-r),y=-(a+r)/(a-r);else if(o===zi)_=-1/(a-r),y=-r/(a-r);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+o);return l[0]=h,l[4]=0,l[8]=0,l[12]=p,l[1]=0,l[5]=f,l[9]=0,l[13]=d,l[2]=0,l[6]=0,l[10]=_,l[14]=y,l[3]=0,l[7]=0,l[11]=0,l[15]=1,this}equals(e){let t=this.elements,n=e.elements;for(let s=0;s<16;s++)if(t[s]!==n[s])return!1;return!0}fromArray(e,t=0){for(let n=0;n<16;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e[t+9]=n[9],e[t+10]=n[10],e[t+11]=n[11],e[t+12]=n[12],e[t+13]=n[13],e[t+14]=n[14],e[t+15]=n[15],e}},hi=new F,qt=new ut,bc=new F(0,0,0),Ac=new F(1,1,1),En=new F,xs=new F,Lt=new F,zo=new ut,Vo=new yn,nn=class i{constructor(e=0,t=0,n=0,s=i.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=t,this._z=n,this._order=s}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,t,n,s=this._order){return this._x=e,this._y=t,this._z=n,this._order=s,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,t=this._order,n=!0){let s=e.elements,r=s[0],a=s[4],o=s[8],c=s[1],l=s[5],h=s[9],f=s[2],p=s[6],d=s[10];switch(t){case"XYZ":this._y=Math.asin(Be(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(-h,d),this._z=Math.atan2(-a,r)):(this._x=Math.atan2(p,l),this._z=0);break;case"YXZ":this._x=Math.asin(-Be(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(o,d),this._z=Math.atan2(c,l)):(this._y=Math.atan2(-f,r),this._z=0);break;case"ZXY":this._x=Math.asin(Be(p,-1,1)),Math.abs(p)<.9999999?(this._y=Math.atan2(-f,d),this._z=Math.atan2(-a,l)):(this._y=0,this._z=Math.atan2(c,r));break;case"ZYX":this._y=Math.asin(-Be(f,-1,1)),Math.abs(f)<.9999999?(this._x=Math.atan2(p,d),this._z=Math.atan2(c,r)):(this._x=0,this._z=Math.atan2(-a,l));break;case"YZX":this._z=Math.asin(Be(c,-1,1)),Math.abs(c)<.9999999?(this._x=Math.atan2(-h,l),this._y=Math.atan2(-f,r)):(this._x=0,this._y=Math.atan2(o,d));break;case"XZY":this._z=Math.asin(-Be(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(p,l),this._y=Math.atan2(o,r)):(this._x=Math.atan2(-h,d),this._y=0);break;default:Ce("Euler: .setFromRotationMatrix() encountered an unknown order: "+t)}return this._order=t,n===!0&&this._onChangeCallback(),this}setFromQuaternion(e,t,n){return zo.makeRotationFromQuaternion(e),this.setFromRotationMatrix(zo,t,n)}setFromVector3(e,t=this._order){return this.set(e.x,e.y,e.z,t)}reorder(e){return Vo.setFromEuler(this),this.setFromQuaternion(Vo,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}};nn.DEFAULT_ORDER="XYZ";var Gi=class{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}},Tc=0,ko=new F,ui=new yn,fn=new ut,vs=new F,Ni=new F,Ec=new F,wc=new yn,Go=new F(1,0,0),Ho=new F(0,1,0),Wo=new F(0,0,1),Xo={type:"added"},Cc={type:"removed"},di={type:"childadded",child:null},ya={type:"childremoved",child:null},Gt=class i extends vn{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:Tc++}),this.uuid=os(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=i.DEFAULT_UP.clone();let e=new F,t=new nn,n=new yn,s=new F(1,1,1);function r(){n.setFromEuler(t,!1)}function a(){t.setFromQuaternion(n,void 0,!1)}t._onChange(r),n._onChange(a),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:t},quaternion:{configurable:!0,enumerable:!0,value:n},scale:{configurable:!0,enumerable:!0,value:s},modelViewMatrix:{value:new ut},normalMatrix:{value:new Ie}}),this.matrix=new ut,this.matrixWorld=new ut,this.matrixAutoUpdate=i.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=i.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new Gi,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.userData={}}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,t){this.quaternion.setFromAxisAngle(e,t)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,t){return ui.setFromAxisAngle(e,t),this.quaternion.multiply(ui),this}rotateOnWorldAxis(e,t){return ui.setFromAxisAngle(e,t),this.quaternion.premultiply(ui),this}rotateX(e){return this.rotateOnAxis(Go,e)}rotateY(e){return this.rotateOnAxis(Ho,e)}rotateZ(e){return this.rotateOnAxis(Wo,e)}translateOnAxis(e,t){return ko.copy(e).applyQuaternion(this.quaternion),this.position.add(ko.multiplyScalar(t)),this}translateX(e){return this.translateOnAxis(Go,e)}translateY(e){return this.translateOnAxis(Ho,e)}translateZ(e){return this.translateOnAxis(Wo,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(fn.copy(this.matrixWorld).invert())}lookAt(e,t,n){e.isVector3?vs.copy(e):vs.set(e,t,n);let s=this.parent;this.updateWorldMatrix(!0,!1),Ni.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?fn.lookAt(Ni,vs,this.up):fn.lookAt(vs,Ni,this.up),this.quaternion.setFromRotationMatrix(fn),s&&(fn.extractRotation(s.matrixWorld),ui.setFromRotationMatrix(fn),this.quaternion.premultiply(ui.invert()))}add(e){if(arguments.length>1){for(let t=0;t<arguments.length;t++)this.add(arguments[t]);return this}return e===this?(Ee("Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(Xo),di.child=e,this.dispatchEvent(di),di.child=null):Ee("Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let n=0;n<arguments.length;n++)this.remove(arguments[n]);return this}let t=this.children.indexOf(e);return t!==-1&&(e.parent=null,this.children.splice(t,1),e.dispatchEvent(Cc),ya.child=e,this.dispatchEvent(ya),ya.child=null),this}removeFromParent(){let e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),fn.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),fn.multiply(e.parent.matrixWorld)),e.applyMatrix4(fn),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(Xo),di.child=e,this.dispatchEvent(di),di.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,t){if(this[e]===t)return this;for(let n=0,s=this.children.length;n<s;n++){let a=this.children[n].getObjectByProperty(e,t);if(a!==void 0)return a}}getObjectsByProperty(e,t,n=[]){this[e]===t&&n.push(this);let s=this.children;for(let r=0,a=s.length;r<a;r++)s[r].getObjectsByProperty(e,t,n);return n}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Ni,e,Ec),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Ni,wc,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);let t=this.matrixWorld.elements;return e.set(t[8],t[9],t[10]).normalize()}raycast(){}traverse(e){e(this);let t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);let t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].traverseVisible(e)}traverseAncestors(e){let t=this.parent;t!==null&&(e(t),t.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale),this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);let t=this.children;for(let n=0,s=t.length;n<s;n++)t[n].updateMatrixWorld(e)}updateWorldMatrix(e,t){let n=this.parent;if(e===!0&&n!==null&&n.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),t===!0){let s=this.children;for(let r=0,a=s.length;r<a;r++)s[r].updateWorldMatrix(!1,!0)}}toJSON(e){let t=e===void 0||typeof e=="string",n={};t&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},n.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});let s={};s.uuid=this.uuid,s.type=this.type,this.name!==""&&(s.name=this.name),this.castShadow===!0&&(s.castShadow=!0),this.receiveShadow===!0&&(s.receiveShadow=!0),this.visible===!1&&(s.visible=!1),this.frustumCulled===!1&&(s.frustumCulled=!1),this.renderOrder!==0&&(s.renderOrder=this.renderOrder),Object.keys(this.userData).length>0&&(s.userData=this.userData),s.layers=this.layers.mask,s.matrix=this.matrix.toArray(),s.up=this.up.toArray(),this.matrixAutoUpdate===!1&&(s.matrixAutoUpdate=!1),this.isInstancedMesh&&(s.type="InstancedMesh",s.count=this.count,s.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(s.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(s.type="BatchedMesh",s.perObjectFrustumCulled=this.perObjectFrustumCulled,s.sortObjects=this.sortObjects,s.drawRanges=this._drawRanges,s.reservedRanges=this._reservedRanges,s.geometryInfo=this._geometryInfo.map(o=>({...o,boundingBox:o.boundingBox?o.boundingBox.toJSON():void 0,boundingSphere:o.boundingSphere?o.boundingSphere.toJSON():void 0})),s.instanceInfo=this._instanceInfo.map(o=>({...o})),s.availableInstanceIds=this._availableInstanceIds.slice(),s.availableGeometryIds=this._availableGeometryIds.slice(),s.nextIndexStart=this._nextIndexStart,s.nextVertexStart=this._nextVertexStart,s.geometryCount=this._geometryCount,s.maxInstanceCount=this._maxInstanceCount,s.maxVertexCount=this._maxVertexCount,s.maxIndexCount=this._maxIndexCount,s.geometryInitialized=this._geometryInitialized,s.matricesTexture=this._matricesTexture.toJSON(e),s.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(s.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(s.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(s.boundingBox=this.boundingBox.toJSON()));function r(o,c){return o[c.uuid]===void 0&&(o[c.uuid]=c.toJSON(e)),c.uuid}if(this.isScene)this.background&&(this.background.isColor?s.background=this.background.toJSON():this.background.isTexture&&(s.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(s.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){s.geometry=r(e.geometries,this.geometry);let o=this.geometry.parameters;if(o!==void 0&&o.shapes!==void 0){let c=o.shapes;if(Array.isArray(c))for(let l=0,h=c.length;l<h;l++){let f=c[l];r(e.shapes,f)}else r(e.shapes,c)}}if(this.isSkinnedMesh&&(s.bindMode=this.bindMode,s.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(r(e.skeletons,this.skeleton),s.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){let o=[];for(let c=0,l=this.material.length;c<l;c++)o.push(r(e.materials,this.material[c]));s.material=o}else s.material=r(e.materials,this.material);if(this.children.length>0){s.children=[];for(let o=0;o<this.children.length;o++)s.children.push(this.children[o].toJSON(e).object)}if(this.animations.length>0){s.animations=[];for(let o=0;o<this.animations.length;o++){let c=this.animations[o];s.animations.push(r(e.animations,c))}}if(t){let o=a(e.geometries),c=a(e.materials),l=a(e.textures),h=a(e.images),f=a(e.shapes),p=a(e.skeletons),d=a(e.animations),_=a(e.nodes);o.length>0&&(n.geometries=o),c.length>0&&(n.materials=c),l.length>0&&(n.textures=l),h.length>0&&(n.images=h),f.length>0&&(n.shapes=f),p.length>0&&(n.skeletons=p),d.length>0&&(n.animations=d),_.length>0&&(n.nodes=_)}return n.object=s,n;function a(o){let c=[];for(let l in o){let h=o[l];delete h.metadata,c.push(h)}return c}}clone(e){return new this.constructor().copy(this,e)}copy(e,t=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),t===!0)for(let n=0;n<e.children.length;n++){let s=e.children[n];this.add(s.clone())}return this}};Gt.DEFAULT_UP=new F(0,1,0);Gt.DEFAULT_MATRIX_AUTO_UPDATE=!0;Gt.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;var Yt=new F,pn=new F,Ma=new F,mn=new F,fi=new F,pi=new F,qo=new F,Sa=new F,ba=new F,Aa=new F,Ta=new ot,Ea=new ot,wa=new ot,Rn=class i{constructor(e=new F,t=new F,n=new F){this.a=e,this.b=t,this.c=n}static getNormal(e,t,n,s){s.subVectors(n,t),Yt.subVectors(e,t),s.cross(Yt);let r=s.lengthSq();return r>0?s.multiplyScalar(1/Math.sqrt(r)):s.set(0,0,0)}static getBarycoord(e,t,n,s,r){Yt.subVectors(s,t),pn.subVectors(n,t),Ma.subVectors(e,t);let a=Yt.dot(Yt),o=Yt.dot(pn),c=Yt.dot(Ma),l=pn.dot(pn),h=pn.dot(Ma),f=a*l-o*o;if(f===0)return r.set(0,0,0),null;let p=1/f,d=(l*c-o*h)*p,_=(a*h-o*c)*p;return r.set(1-d-_,_,d)}static containsPoint(e,t,n,s){return this.getBarycoord(e,t,n,s,mn)===null?!1:mn.x>=0&&mn.y>=0&&mn.x+mn.y<=1}static getInterpolation(e,t,n,s,r,a,o,c){return this.getBarycoord(e,t,n,s,mn)===null?(c.x=0,c.y=0,"z"in c&&(c.z=0),"w"in c&&(c.w=0),null):(c.setScalar(0),c.addScaledVector(r,mn.x),c.addScaledVector(a,mn.y),c.addScaledVector(o,mn.z),c)}static getInterpolatedAttribute(e,t,n,s,r,a){return Ta.setScalar(0),Ea.setScalar(0),wa.setScalar(0),Ta.fromBufferAttribute(e,t),Ea.fromBufferAttribute(e,n),wa.fromBufferAttribute(e,s),a.setScalar(0),a.addScaledVector(Ta,r.x),a.addScaledVector(Ea,r.y),a.addScaledVector(wa,r.z),a}static isFrontFacing(e,t,n,s){return Yt.subVectors(n,t),pn.subVectors(e,t),Yt.cross(pn).dot(s)<0}set(e,t,n){return this.a.copy(e),this.b.copy(t),this.c.copy(n),this}setFromPointsAndIndices(e,t,n,s){return this.a.copy(e[t]),this.b.copy(e[n]),this.c.copy(e[s]),this}setFromAttributeAndIndices(e,t,n,s){return this.a.fromBufferAttribute(e,t),this.b.fromBufferAttribute(e,n),this.c.fromBufferAttribute(e,s),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return Yt.subVectors(this.c,this.b),pn.subVectors(this.a,this.b),Yt.cross(pn).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return i.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,t){return i.getBarycoord(e,this.a,this.b,this.c,t)}getInterpolation(e,t,n,s,r){return i.getInterpolation(e,this.a,this.b,this.c,t,n,s,r)}containsPoint(e){return i.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return i.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,t){let n=this.a,s=this.b,r=this.c,a,o;fi.subVectors(s,n),pi.subVectors(r,n),Sa.subVectors(e,n);let c=fi.dot(Sa),l=pi.dot(Sa);if(c<=0&&l<=0)return t.copy(n);ba.subVectors(e,s);let h=fi.dot(ba),f=pi.dot(ba);if(h>=0&&f<=h)return t.copy(s);let p=c*f-h*l;if(p<=0&&c>=0&&h<=0)return a=c/(c-h),t.copy(n).addScaledVector(fi,a);Aa.subVectors(e,r);let d=fi.dot(Aa),_=pi.dot(Aa);if(_>=0&&d<=_)return t.copy(r);let y=d*l-c*_;if(y<=0&&l>=0&&_<=0)return o=l/(l-_),t.copy(n).addScaledVector(pi,o);let m=h*_-d*f;if(m<=0&&f-h>=0&&d-_>=0)return qo.subVectors(r,s),o=(f-h)/(f-h+(d-_)),t.copy(s).addScaledVector(qo,o);let u=1/(m+y+p);return a=y*u,o=p*u,t.copy(n).addScaledVector(fi,a).addScaledVector(pi,o)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}},Dl={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},wn={h:0,s:0,l:0},ys={h:0,s:0,l:0};function Ca(i,e,t){return t<0&&(t+=1),t>1&&(t-=1),t<1/6?i+(e-i)*6*t:t<1/2?e:t<2/3?i+(e-i)*6*(2/3-t):i}var He=class{constructor(e,t,n){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,t,n)}set(e,t,n){if(t===void 0&&n===void 0){let s=e;s&&s.isColor?this.copy(s):typeof s=="number"?this.setHex(s):typeof s=="string"&&this.setStyle(s)}else this.setRGB(e,t,n);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,t=bt){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,ze.colorSpaceToWorking(this,t),this}setRGB(e,t,n,s=ze.workingColorSpace){return this.r=e,this.g=t,this.b=n,ze.colorSpaceToWorking(this,s),this}setHSL(e,t,n,s=ze.workingColorSpace){if(e=xc(e,1),t=Be(t,0,1),n=Be(n,0,1),t===0)this.r=this.g=this.b=n;else{let r=n<=.5?n*(1+t):n+t-n*t,a=2*n-r;this.r=Ca(a,r,e+1/3),this.g=Ca(a,r,e),this.b=Ca(a,r,e-1/3)}return ze.colorSpaceToWorking(this,s),this}setStyle(e,t=bt){function n(r){r!==void 0&&parseFloat(r)<1&&Ce("Color: Alpha component of "+e+" will be ignored.")}let s;if(s=/^(\w+)\(([^\)]*)\)/.exec(e)){let r,a=s[1],o=s[2];switch(a){case"rgb":case"rgba":if(r=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(255,parseInt(r[1],10))/255,Math.min(255,parseInt(r[2],10))/255,Math.min(255,parseInt(r[3],10))/255,t);if(r=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setRGB(Math.min(100,parseInt(r[1],10))/100,Math.min(100,parseInt(r[2],10))/100,Math.min(100,parseInt(r[3],10))/100,t);break;case"hsl":case"hsla":if(r=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(r[4]),this.setHSL(parseFloat(r[1])/360,parseFloat(r[2])/100,parseFloat(r[3])/100,t);break;default:Ce("Color: Unknown color model "+e)}}else if(s=/^\#([A-Fa-f\d]+)$/.exec(e)){let r=s[1],a=r.length;if(a===3)return this.setRGB(parseInt(r.charAt(0),16)/15,parseInt(r.charAt(1),16)/15,parseInt(r.charAt(2),16)/15,t);if(a===6)return this.setHex(parseInt(r,16),t);Ce("Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,t);return this}setColorName(e,t=bt){let n=Dl[e.toLowerCase()];return n!==void 0?this.setHex(n,t):Ce("Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=_n(e.r),this.g=_n(e.g),this.b=_n(e.b),this}copyLinearToSRGB(e){return this.r=xi(e.r),this.g=xi(e.g),this.b=xi(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=bt){return ze.workingToColorSpace(vt.copy(this),e),Math.round(Be(vt.r*255,0,255))*65536+Math.round(Be(vt.g*255,0,255))*256+Math.round(Be(vt.b*255,0,255))}getHexString(e=bt){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,t=ze.workingColorSpace){ze.workingToColorSpace(vt.copy(this),t);let n=vt.r,s=vt.g,r=vt.b,a=Math.max(n,s,r),o=Math.min(n,s,r),c,l,h=(o+a)/2;if(o===a)c=0,l=0;else{let f=a-o;switch(l=h<=.5?f/(a+o):f/(2-a-o),a){case n:c=(s-r)/f+(s<r?6:0);break;case s:c=(r-n)/f+2;break;case r:c=(n-s)/f+4;break}c/=6}return e.h=c,e.s=l,e.l=h,e}getRGB(e,t=ze.workingColorSpace){return ze.workingToColorSpace(vt.copy(this),t),e.r=vt.r,e.g=vt.g,e.b=vt.b,e}getStyle(e=bt){ze.workingToColorSpace(vt.copy(this),e);let t=vt.r,n=vt.g,s=vt.b;return e!==bt?`color(${e} ${t.toFixed(3)} ${n.toFixed(3)} ${s.toFixed(3)})`:`rgb(${Math.round(t*255)},${Math.round(n*255)},${Math.round(s*255)})`}offsetHSL(e,t,n){return this.getHSL(wn),this.setHSL(wn.h+e,wn.s+t,wn.l+n)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,t){return this.r=e.r+t.r,this.g=e.g+t.g,this.b=e.b+t.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,t){return this.r+=(e.r-this.r)*t,this.g+=(e.g-this.g)*t,this.b+=(e.b-this.b)*t,this}lerpColors(e,t,n){return this.r=e.r+(t.r-e.r)*n,this.g=e.g+(t.g-e.g)*n,this.b=e.b+(t.b-e.b)*n,this}lerpHSL(e,t){this.getHSL(wn),e.getHSL(ys);let n=ha(wn.h,ys.h,t),s=ha(wn.s,ys.s,t),r=ha(wn.l,ys.l,t);return this.setHSL(n,s,r),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){let t=this.r,n=this.g,s=this.b,r=e.elements;return this.r=r[0]*t+r[3]*n+r[6]*s,this.g=r[1]*t+r[4]*n+r[7]*s,this.b=r[2]*t+r[5]*n+r[8]*s,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,t=0){return this.r=e[t],this.g=e[t+1],this.b=e[t+2],this}toArray(e=[],t=0){return e[t]=this.r,e[t+1]=this.g,e[t+2]=this.b,e}fromBufferAttribute(e,t){return this.r=e.getX(t),this.g=e.getY(t),this.b=e.getZ(t),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}},vt=new He;He.NAMES=Dl;var Rc=0,Jn=class extends vn{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:Rc++}),this.uuid=os(),this.name="",this.type="Material",this.blending=qn,this.side=xn,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=Ls,this.blendDst=Ds,this.blendEquation=In,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new He(0,0,0),this.blendAlpha=0,this.depthFunc=Yn,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=Na,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=Xn,this.stencilZFail=Xn,this.stencilZPass=Xn,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(let t in e){let n=e[t];if(n===void 0){Ce(`Material: parameter '${t}' has value of undefined.`);continue}let s=this[t];if(s===void 0){Ce(`Material: '${t}' is not a property of THREE.${this.type}.`);continue}s&&s.isColor?s.set(n):s&&s.isVector3&&n&&n.isVector3?s.copy(n):this[t]=n}}toJSON(e){let t=e===void 0||typeof e=="string";t&&(e={textures:{},images:{}});let n={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};n.uuid=this.uuid,n.type=this.type,this.name!==""&&(n.name=this.name),this.color&&this.color.isColor&&(n.color=this.color.getHex()),this.roughness!==void 0&&(n.roughness=this.roughness),this.metalness!==void 0&&(n.metalness=this.metalness),this.sheen!==void 0&&(n.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(n.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(n.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(n.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&this.emissiveIntensity!==1&&(n.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(n.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(n.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(n.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(n.shininess=this.shininess),this.clearcoat!==void 0&&(n.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(n.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(n.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(n.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(n.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,n.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(n.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(n.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(n.dispersion=this.dispersion),this.iridescence!==void 0&&(n.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(n.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(n.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(n.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(n.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(n.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(n.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(n.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(n.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(n.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(n.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(n.lightMap=this.lightMap.toJSON(e).uuid,n.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(n.aoMap=this.aoMap.toJSON(e).uuid,n.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(n.bumpMap=this.bumpMap.toJSON(e).uuid,n.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(n.normalMap=this.normalMap.toJSON(e).uuid,n.normalMapType=this.normalMapType,n.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(n.displacementMap=this.displacementMap.toJSON(e).uuid,n.displacementScale=this.displacementScale,n.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(n.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(n.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(n.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(n.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(n.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(n.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(n.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(n.combine=this.combine)),this.envMapRotation!==void 0&&(n.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(n.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(n.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(n.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(n.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(n.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(n.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(n.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(n.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&this.attenuationDistance!==1/0&&(n.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(n.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(n.size=this.size),this.shadowSide!==null&&(n.shadowSide=this.shadowSide),this.sizeAttenuation!==void 0&&(n.sizeAttenuation=this.sizeAttenuation),this.blending!==qn&&(n.blending=this.blending),this.side!==xn&&(n.side=this.side),this.vertexColors===!0&&(n.vertexColors=!0),this.opacity<1&&(n.opacity=this.opacity),this.transparent===!0&&(n.transparent=!0),this.blendSrc!==Ls&&(n.blendSrc=this.blendSrc),this.blendDst!==Ds&&(n.blendDst=this.blendDst),this.blendEquation!==In&&(n.blendEquation=this.blendEquation),this.blendSrcAlpha!==null&&(n.blendSrcAlpha=this.blendSrcAlpha),this.blendDstAlpha!==null&&(n.blendDstAlpha=this.blendDstAlpha),this.blendEquationAlpha!==null&&(n.blendEquationAlpha=this.blendEquationAlpha),this.blendColor&&this.blendColor.isColor&&(n.blendColor=this.blendColor.getHex()),this.blendAlpha!==0&&(n.blendAlpha=this.blendAlpha),this.depthFunc!==Yn&&(n.depthFunc=this.depthFunc),this.depthTest===!1&&(n.depthTest=this.depthTest),this.depthWrite===!1&&(n.depthWrite=this.depthWrite),this.colorWrite===!1&&(n.colorWrite=this.colorWrite),this.stencilWriteMask!==255&&(n.stencilWriteMask=this.stencilWriteMask),this.stencilFunc!==Na&&(n.stencilFunc=this.stencilFunc),this.stencilRef!==0&&(n.stencilRef=this.stencilRef),this.stencilFuncMask!==255&&(n.stencilFuncMask=this.stencilFuncMask),this.stencilFail!==Xn&&(n.stencilFail=this.stencilFail),this.stencilZFail!==Xn&&(n.stencilZFail=this.stencilZFail),this.stencilZPass!==Xn&&(n.stencilZPass=this.stencilZPass),this.stencilWrite===!0&&(n.stencilWrite=this.stencilWrite),this.rotation!==void 0&&this.rotation!==0&&(n.rotation=this.rotation),this.polygonOffset===!0&&(n.polygonOffset=!0),this.polygonOffsetFactor!==0&&(n.polygonOffsetFactor=this.polygonOffsetFactor),this.polygonOffsetUnits!==0&&(n.polygonOffsetUnits=this.polygonOffsetUnits),this.linewidth!==void 0&&this.linewidth!==1&&(n.linewidth=this.linewidth),this.dashSize!==void 0&&(n.dashSize=this.dashSize),this.gapSize!==void 0&&(n.gapSize=this.gapSize),this.scale!==void 0&&(n.scale=this.scale),this.dithering===!0&&(n.dithering=!0),this.alphaTest>0&&(n.alphaTest=this.alphaTest),this.alphaHash===!0&&(n.alphaHash=!0),this.alphaToCoverage===!0&&(n.alphaToCoverage=!0),this.premultipliedAlpha===!0&&(n.premultipliedAlpha=!0),this.forceSinglePass===!0&&(n.forceSinglePass=!0),this.allowOverride===!1&&(n.allowOverride=!1),this.wireframe===!0&&(n.wireframe=!0),this.wireframeLinewidth>1&&(n.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!=="round"&&(n.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!=="round"&&(n.wireframeLinejoin=this.wireframeLinejoin),this.flatShading===!0&&(n.flatShading=!0),this.visible===!1&&(n.visible=!1),this.toneMapped===!1&&(n.toneMapped=!1),this.fog===!1&&(n.fog=!1),Object.keys(this.userData).length>0&&(n.userData=this.userData);function s(r){let a=[];for(let o in r){let c=r[o];delete c.metadata,a.push(c)}return a}if(t){let r=s(e.textures),a=s(e.images);r.length>0&&(n.textures=r),a.length>0&&(n.images=a)}return n}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;let t=e.clippingPlanes,n=null;if(t!==null){let s=t.length;n=new Array(s);for(let r=0;r!==s;++r)n[r]=t[r].clone()}return this.clippingPlanes=n,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.allowOverride=e.allowOverride,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}},$n=class extends Jn{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new He(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new nn,this.combine=Ga,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}};var ht=new F,Ms=new Je,Ic=0,Ut=class{constructor(e,t,n=!1){if(Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:Ic++}),this.name="",this.array=e,this.itemSize=t,this.count=e!==void 0?e.length/t:0,this.normalized=n,this.usage=Fa,this.updateRanges=[],this.gpuType=Kt,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,t,n){e*=this.itemSize,n*=t.itemSize;for(let s=0,r=this.itemSize;s<r;s++)this.array[e+s]=t.array[n+s];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let t=0,n=this.count;t<n;t++)Ms.fromBufferAttribute(this,t),Ms.applyMatrix3(e),this.setXY(t,Ms.x,Ms.y);else if(this.itemSize===3)for(let t=0,n=this.count;t<n;t++)ht.fromBufferAttribute(this,t),ht.applyMatrix3(e),this.setXYZ(t,ht.x,ht.y,ht.z);return this}applyMatrix4(e){for(let t=0,n=this.count;t<n;t++)ht.fromBufferAttribute(this,t),ht.applyMatrix4(e),this.setXYZ(t,ht.x,ht.y,ht.z);return this}applyNormalMatrix(e){for(let t=0,n=this.count;t<n;t++)ht.fromBufferAttribute(this,t),ht.applyNormalMatrix(e),this.setXYZ(t,ht.x,ht.y,ht.z);return this}transformDirection(e){for(let t=0,n=this.count;t<n;t++)ht.fromBufferAttribute(this,t),ht.transformDirection(e),this.setXYZ(t,ht.x,ht.y,ht.z);return this}set(e,t=0){return this.array.set(e,t),this}getComponent(e,t){let n=this.array[e*this.itemSize+t];return this.normalized&&(n=Li(n,this.array)),n}setComponent(e,t,n){return this.normalized&&(n=Ct(n,this.array)),this.array[e*this.itemSize+t]=n,this}getX(e){let t=this.array[e*this.itemSize];return this.normalized&&(t=Li(t,this.array)),t}setX(e,t){return this.normalized&&(t=Ct(t,this.array)),this.array[e*this.itemSize]=t,this}getY(e){let t=this.array[e*this.itemSize+1];return this.normalized&&(t=Li(t,this.array)),t}setY(e,t){return this.normalized&&(t=Ct(t,this.array)),this.array[e*this.itemSize+1]=t,this}getZ(e){let t=this.array[e*this.itemSize+2];return this.normalized&&(t=Li(t,this.array)),t}setZ(e,t){return this.normalized&&(t=Ct(t,this.array)),this.array[e*this.itemSize+2]=t,this}getW(e){let t=this.array[e*this.itemSize+3];return this.normalized&&(t=Li(t,this.array)),t}setW(e,t){return this.normalized&&(t=Ct(t,this.array)),this.array[e*this.itemSize+3]=t,this}setXY(e,t,n){return e*=this.itemSize,this.normalized&&(t=Ct(t,this.array),n=Ct(n,this.array)),this.array[e+0]=t,this.array[e+1]=n,this}setXYZ(e,t,n,s){return e*=this.itemSize,this.normalized&&(t=Ct(t,this.array),n=Ct(n,this.array),s=Ct(s,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=s,this}setXYZW(e,t,n,s,r){return e*=this.itemSize,this.normalized&&(t=Ct(t,this.array),n=Ct(n,this.array),s=Ct(s,this.array),r=Ct(r,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=s,this.array[e+3]=r,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){let e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return this.name!==""&&(e.name=this.name),this.usage!==Fa&&(e.usage=this.usage),e}};var Hi=class extends Ut{constructor(e,t,n){super(new Uint16Array(e),t,n)}};var Wi=class extends Ut{constructor(e,t,n){super(new Uint32Array(e),t,n)}};var kt=class extends Ut{constructor(e,t,n){super(new Float32Array(e),t,n)}},Pc=0,Vt=new ut,Ra=new Gt,mi=new F,Dt=new Pn,Fi=new Pn,mt=new F,sn=class i extends vn{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:Pc++}),this.uuid=os(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.indirectOffset=0,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={}}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new(ro(e)?Wi:Hi)(e,1):this.index=e,this}setIndirect(e,t=0){return this.indirect=e,this.indirectOffset=t,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,t){return this.attributes[e]=t,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,t,n=0){this.groups.push({start:e,count:t,materialIndex:n})}clearGroups(){this.groups=[]}setDrawRange(e,t){this.drawRange.start=e,this.drawRange.count=t}applyMatrix4(e){let t=this.attributes.position;t!==void 0&&(t.applyMatrix4(e),t.needsUpdate=!0);let n=this.attributes.normal;if(n!==void 0){let r=new Ie().getNormalMatrix(e);n.applyNormalMatrix(r),n.needsUpdate=!0}let s=this.attributes.tangent;return s!==void 0&&(s.transformDirection(e),s.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}applyQuaternion(e){return Vt.makeRotationFromQuaternion(e),this.applyMatrix4(Vt),this}rotateX(e){return Vt.makeRotationX(e),this.applyMatrix4(Vt),this}rotateY(e){return Vt.makeRotationY(e),this.applyMatrix4(Vt),this}rotateZ(e){return Vt.makeRotationZ(e),this.applyMatrix4(Vt),this}translate(e,t,n){return Vt.makeTranslation(e,t,n),this.applyMatrix4(Vt),this}scale(e,t,n){return Vt.makeScale(e,t,n),this.applyMatrix4(Vt),this}lookAt(e){return Ra.lookAt(e),Ra.updateMatrix(),this.applyMatrix4(Ra.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(mi).negate(),this.translate(mi.x,mi.y,mi.z),this}setFromPoints(e){let t=this.getAttribute("position");if(t===void 0){let n=[];for(let s=0,r=e.length;s<r;s++){let a=e[s];n.push(a.x,a.y,a.z||0)}this.setAttribute("position",new kt(n,3))}else{let n=Math.min(e.length,t.count);for(let s=0;s<n;s++){let r=e[s];t.setXYZ(s,r.x,r.y,r.z||0)}e.length>t.count&&Ce("BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),t.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new Pn);let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){Ee("BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new F(-1/0,-1/0,-1/0),new F(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),t)for(let n=0,s=t.length;n<s;n++){let r=t[n];Dt.setFromBufferAttribute(r),this.morphTargetsRelative?(mt.addVectors(this.boundingBox.min,Dt.min),this.boundingBox.expandByPoint(mt),mt.addVectors(this.boundingBox.max,Dt.max),this.boundingBox.expandByPoint(mt)):(this.boundingBox.expandByPoint(Dt.min),this.boundingBox.expandByPoint(Dt.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&Ee('BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new Si);let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){Ee("BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new F,1/0);return}if(e){let n=this.boundingSphere.center;if(Dt.setFromBufferAttribute(e),t)for(let r=0,a=t.length;r<a;r++){let o=t[r];Fi.setFromBufferAttribute(o),this.morphTargetsRelative?(mt.addVectors(Dt.min,Fi.min),Dt.expandByPoint(mt),mt.addVectors(Dt.max,Fi.max),Dt.expandByPoint(mt)):(Dt.expandByPoint(Fi.min),Dt.expandByPoint(Fi.max))}Dt.getCenter(n);let s=0;for(let r=0,a=e.count;r<a;r++)mt.fromBufferAttribute(e,r),s=Math.max(s,n.distanceToSquared(mt));if(t)for(let r=0,a=t.length;r<a;r++){let o=t[r],c=this.morphTargetsRelative;for(let l=0,h=o.count;l<h;l++)mt.fromBufferAttribute(o,l),c&&(mi.fromBufferAttribute(e,l),mt.add(mi)),s=Math.max(s,n.distanceToSquared(mt))}this.boundingSphere.radius=Math.sqrt(s),isNaN(this.boundingSphere.radius)&&Ee('BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){let e=this.index,t=this.attributes;if(e===null||t.position===void 0||t.normal===void 0||t.uv===void 0){Ee("BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}let n=t.position,s=t.normal,r=t.uv;this.hasAttribute("tangent")===!1&&this.setAttribute("tangent",new Ut(new Float32Array(4*n.count),4));let a=this.getAttribute("tangent"),o=[],c=[];for(let B=0;B<n.count;B++)o[B]=new F,c[B]=new F;let l=new F,h=new F,f=new F,p=new Je,d=new Je,_=new Je,y=new F,m=new F;function u(B,v,M){l.fromBufferAttribute(n,B),h.fromBufferAttribute(n,v),f.fromBufferAttribute(n,M),p.fromBufferAttribute(r,B),d.fromBufferAttribute(r,v),_.fromBufferAttribute(r,M),h.sub(l),f.sub(l),d.sub(p),_.sub(p);let L=1/(d.x*_.y-_.x*d.y);isFinite(L)&&(y.copy(h).multiplyScalar(_.y).addScaledVector(f,-d.y).multiplyScalar(L),m.copy(f).multiplyScalar(d.x).addScaledVector(h,-_.x).multiplyScalar(L),o[B].add(y),o[v].add(y),o[M].add(y),c[B].add(m),c[v].add(m),c[M].add(m))}let b=this.groups;b.length===0&&(b=[{start:0,count:e.count}]);for(let B=0,v=b.length;B<v;++B){let M=b[B],L=M.start,V=M.count;for(let z=L,W=L+V;z<W;z+=3)u(e.getX(z+0),e.getX(z+1),e.getX(z+2))}let T=new F,A=new F,E=new F,w=new F;function I(B){E.fromBufferAttribute(s,B),w.copy(E);let v=o[B];T.copy(v),T.sub(E.multiplyScalar(E.dot(v))).normalize(),A.crossVectors(w,v);let L=A.dot(c[B])<0?-1:1;a.setXYZW(B,T.x,T.y,T.z,L)}for(let B=0,v=b.length;B<v;++B){let M=b[B],L=M.start,V=M.count;for(let z=L,W=L+V;z<W;z+=3)I(e.getX(z+0)),I(e.getX(z+1)),I(e.getX(z+2))}}computeVertexNormals(){let e=this.index,t=this.getAttribute("position");if(t!==void 0){let n=this.getAttribute("normal");if(n===void 0)n=new Ut(new Float32Array(t.count*3),3),this.setAttribute("normal",n);else for(let p=0,d=n.count;p<d;p++)n.setXYZ(p,0,0,0);let s=new F,r=new F,a=new F,o=new F,c=new F,l=new F,h=new F,f=new F;if(e)for(let p=0,d=e.count;p<d;p+=3){let _=e.getX(p+0),y=e.getX(p+1),m=e.getX(p+2);s.fromBufferAttribute(t,_),r.fromBufferAttribute(t,y),a.fromBufferAttribute(t,m),h.subVectors(a,r),f.subVectors(s,r),h.cross(f),o.fromBufferAttribute(n,_),c.fromBufferAttribute(n,y),l.fromBufferAttribute(n,m),o.add(h),c.add(h),l.add(h),n.setXYZ(_,o.x,o.y,o.z),n.setXYZ(y,c.x,c.y,c.z),n.setXYZ(m,l.x,l.y,l.z)}else for(let p=0,d=t.count;p<d;p+=3)s.fromBufferAttribute(t,p+0),r.fromBufferAttribute(t,p+1),a.fromBufferAttribute(t,p+2),h.subVectors(a,r),f.subVectors(s,r),h.cross(f),n.setXYZ(p+0,h.x,h.y,h.z),n.setXYZ(p+1,h.x,h.y,h.z),n.setXYZ(p+2,h.x,h.y,h.z);this.normalizeNormals(),n.needsUpdate=!0}}normalizeNormals(){let e=this.attributes.normal;for(let t=0,n=e.count;t<n;t++)mt.fromBufferAttribute(e,t),mt.normalize(),e.setXYZ(t,mt.x,mt.y,mt.z)}toNonIndexed(){function e(o,c){let l=o.array,h=o.itemSize,f=o.normalized,p=new l.constructor(c.length*h),d=0,_=0;for(let y=0,m=c.length;y<m;y++){o.isInterleavedBufferAttribute?d=c[y]*o.data.stride+o.offset:d=c[y]*h;for(let u=0;u<h;u++)p[_++]=l[d++]}return new Ut(p,h,f)}if(this.index===null)return Ce("BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;let t=new i,n=this.index.array,s=this.attributes;for(let o in s){let c=s[o],l=e(c,n);t.setAttribute(o,l)}let r=this.morphAttributes;for(let o in r){let c=[],l=r[o];for(let h=0,f=l.length;h<f;h++){let p=l[h],d=e(p,n);c.push(d)}t.morphAttributes[o]=c}t.morphTargetsRelative=this.morphTargetsRelative;let a=this.groups;for(let o=0,c=a.length;o<c;o++){let l=a[o];t.addGroup(l.start,l.count,l.materialIndex)}return t}toJSON(){let e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.type,this.name!==""&&(e.name=this.name),Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0){let c=this.parameters;for(let l in c)c[l]!==void 0&&(e[l]=c[l]);return e}e.data={attributes:{}};let t=this.index;t!==null&&(e.data.index={type:t.array.constructor.name,array:Array.prototype.slice.call(t.array)});let n=this.attributes;for(let c in n){let l=n[c];e.data.attributes[c]=l.toJSON(e.data)}let s={},r=!1;for(let c in this.morphAttributes){let l=this.morphAttributes[c],h=[];for(let f=0,p=l.length;f<p;f++){let d=l[f];h.push(d.toJSON(e.data))}h.length>0&&(s[c]=h,r=!0)}r&&(e.data.morphAttributes=s,e.data.morphTargetsRelative=this.morphTargetsRelative);let a=this.groups;a.length>0&&(e.data.groups=JSON.parse(JSON.stringify(a)));let o=this.boundingSphere;return o!==null&&(e.data.boundingSphere=o.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;let t={};this.name=e.name;let n=e.index;n!==null&&this.setIndex(n.clone());let s=e.attributes;for(let l in s){let h=s[l];this.setAttribute(l,h.clone(t))}let r=e.morphAttributes;for(let l in r){let h=[],f=r[l];for(let p=0,d=f.length;p<d;p++)h.push(f[p].clone(t));this.morphAttributes[l]=h}this.morphTargetsRelative=e.morphTargetsRelative;let a=e.groups;for(let l=0,h=a.length;l<h;l++){let f=a[l];this.addGroup(f.start,f.count,f.materialIndex)}let o=e.boundingBox;o!==null&&(this.boundingBox=o.clone());let c=e.boundingSphere;return c!==null&&(this.boundingSphere=c.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this}dispose(){this.dispatchEvent({type:"dispose"})}},Yo=new ut,Hn=new ks,Ss=new Si,Zo=new F,bs=new F,As=new F,Ts=new F,Ia=new F,Es=new F,Jo=new F,ws=new F,Rt=class extends Gt{constructor(e=new sn,t=new $n){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let s=t[n[0]];if(s!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let r=0,a=s.length;r<a;r++){let o=s[r].name||String(r);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=r}}}}getVertexPosition(e,t){let n=this.geometry,s=n.attributes.position,r=n.morphAttributes.position,a=n.morphTargetsRelative;t.fromBufferAttribute(s,e);let o=this.morphTargetInfluences;if(r&&o){Es.set(0,0,0);for(let c=0,l=r.length;c<l;c++){let h=o[c],f=r[c];h!==0&&(Ia.fromBufferAttribute(f,e),a?Es.addScaledVector(Ia,h):Es.addScaledVector(Ia.sub(t),h))}t.add(Es)}return t}raycast(e,t){let n=this.geometry,s=this.material,r=this.matrixWorld;s!==void 0&&(n.boundingSphere===null&&n.computeBoundingSphere(),Ss.copy(n.boundingSphere),Ss.applyMatrix4(r),Hn.copy(e.ray).recast(e.near),!(Ss.containsPoint(Hn.origin)===!1&&(Hn.intersectSphere(Ss,Zo)===null||Hn.origin.distanceToSquared(Zo)>(e.far-e.near)**2))&&(Yo.copy(r).invert(),Hn.copy(e.ray).applyMatrix4(Yo),!(n.boundingBox!==null&&Hn.intersectsBox(n.boundingBox)===!1)&&this._computeIntersections(e,t,Hn)))}_computeIntersections(e,t,n){let s,r=this.geometry,a=this.material,o=r.index,c=r.attributes.position,l=r.attributes.uv,h=r.attributes.uv1,f=r.attributes.normal,p=r.groups,d=r.drawRange;if(o!==null)if(Array.isArray(a))for(let _=0,y=p.length;_<y;_++){let m=p[_],u=a[m.materialIndex],b=Math.max(m.start,d.start),T=Math.min(o.count,Math.min(m.start+m.count,d.start+d.count));for(let A=b,E=T;A<E;A+=3){let w=o.getX(A),I=o.getX(A+1),B=o.getX(A+2);s=Cs(this,u,e,n,l,h,f,w,I,B),s&&(s.faceIndex=Math.floor(A/3),s.face.materialIndex=m.materialIndex,t.push(s))}}else{let _=Math.max(0,d.start),y=Math.min(o.count,d.start+d.count);for(let m=_,u=y;m<u;m+=3){let b=o.getX(m),T=o.getX(m+1),A=o.getX(m+2);s=Cs(this,a,e,n,l,h,f,b,T,A),s&&(s.faceIndex=Math.floor(m/3),t.push(s))}}else if(c!==void 0)if(Array.isArray(a))for(let _=0,y=p.length;_<y;_++){let m=p[_],u=a[m.materialIndex],b=Math.max(m.start,d.start),T=Math.min(c.count,Math.min(m.start+m.count,d.start+d.count));for(let A=b,E=T;A<E;A+=3){let w=A,I=A+1,B=A+2;s=Cs(this,u,e,n,l,h,f,w,I,B),s&&(s.faceIndex=Math.floor(A/3),s.face.materialIndex=m.materialIndex,t.push(s))}}else{let _=Math.max(0,d.start),y=Math.min(c.count,d.start+d.count);for(let m=_,u=y;m<u;m+=3){let b=m,T=m+1,A=m+2;s=Cs(this,a,e,n,l,h,f,b,T,A),s&&(s.faceIndex=Math.floor(m/3),t.push(s))}}}};function Lc(i,e,t,n,s,r,a,o){let c;if(e.side===Tt?c=n.intersectTriangle(a,r,s,!0,o):c=n.intersectTriangle(s,r,a,e.side===xn,o),c===null)return null;ws.copy(o),ws.applyMatrix4(i.matrixWorld);let l=t.ray.origin.distanceTo(ws);return l<t.near||l>t.far?null:{distance:l,point:ws.clone(),object:i}}function Cs(i,e,t,n,s,r,a,o,c,l){i.getVertexPosition(o,bs),i.getVertexPosition(c,As),i.getVertexPosition(l,Ts);let h=Lc(i,e,t,n,bs,As,Ts,Jo);if(h){let f=new F;Rn.getBarycoord(Jo,bs,As,Ts,f),s&&(h.uv=Rn.getInterpolatedAttribute(s,o,c,l,f,new Je)),r&&(h.uv1=Rn.getInterpolatedAttribute(r,o,c,l,f,new Je)),a&&(h.normal=Rn.getInterpolatedAttribute(a,o,c,l,f,new F),h.normal.dot(n.direction)>0&&h.normal.multiplyScalar(-1));let p={a:o,b:c,c:l,normal:new F,materialIndex:0};Rn.getNormal(bs,As,Ts,p.normal),h.face=p,h.barycoord=f}return h}var bi=class i extends sn{constructor(e=1,t=1,n=1,s=1,r=1,a=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:t,depth:n,widthSegments:s,heightSegments:r,depthSegments:a};let o=this;s=Math.floor(s),r=Math.floor(r),a=Math.floor(a);let c=[],l=[],h=[],f=[],p=0,d=0;_("z","y","x",-1,-1,n,t,e,a,r,0),_("z","y","x",1,-1,n,t,-e,a,r,1),_("x","z","y",1,1,e,n,t,s,a,2),_("x","z","y",1,-1,e,n,-t,s,a,3),_("x","y","z",1,-1,e,t,n,s,r,4),_("x","y","z",-1,-1,e,t,-n,s,r,5),this.setIndex(c),this.setAttribute("position",new kt(l,3)),this.setAttribute("normal",new kt(h,3)),this.setAttribute("uv",new kt(f,2));function _(y,m,u,b,T,A,E,w,I,B,v){let M=A/I,L=E/B,V=A/2,z=E/2,W=w/2,Y=I+1,k=B+1,H=0,$=0,he=new F;for(let ae=0;ae<k;ae++){let ue=ae*L-z;for(let Fe=0;Fe<Y;Fe++){let De=Fe*M-V;he[y]=De*b,he[m]=ue*T,he[u]=W,l.push(he.x,he.y,he.z),he[y]=0,he[m]=0,he[u]=w>0?1:-1,h.push(he.x,he.y,he.z),f.push(Fe/I),f.push(1-ae/B),H+=1}}for(let ae=0;ae<B;ae++)for(let ue=0;ue<I;ue++){let Fe=p+ue+Y*ae,De=p+ue+Y*(ae+1),st=p+(ue+1)+Y*(ae+1),nt=p+(ue+1)+Y*ae;c.push(Fe,De,nt),c.push(De,st,nt),$+=6}o.addGroup(d,$,v),d+=$,p+=H}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}};function ti(i){let e={};for(let t in i){e[t]={};for(let n in i[t]){let s=i[t][n];s&&(s.isColor||s.isMatrix3||s.isMatrix4||s.isVector2||s.isVector3||s.isVector4||s.isTexture||s.isQuaternion)?s.isRenderTargetTexture?(Ce("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[t][n]=null):e[t][n]=s.clone():Array.isArray(s)?e[t][n]=s.slice():e[t][n]=s}}return e}function Mt(i){let e={};for(let t=0;t<i.length;t++){let n=ti(i[t]);for(let s in n)e[s]=n[s]}return e}function Dc(i){let e=[];for(let t=0;t<i.length;t++)e.push(i[t].clone());return e}function oo(i){let e=i.getRenderTarget();return e===null?i.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:ze.workingColorSpace}var Ul={clone:ti,merge:Mt},Uc=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,Nc=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`,Ft=class extends Jn{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=Uc,this.fragmentShader=Nc,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=ti(e.uniforms),this.uniformsGroups=Dc(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this.defaultAttributeValues=Object.assign({},e.defaultAttributeValues),this.index0AttributeName=e.index0AttributeName,this.uniformsNeedUpdate=e.uniformsNeedUpdate,this}toJSON(e){let t=super.toJSON(e);t.glslVersion=this.glslVersion,t.uniforms={};for(let s in this.uniforms){let a=this.uniforms[s].value;a&&a.isTexture?t.uniforms[s]={type:"t",value:a.toJSON(e).uuid}:a&&a.isColor?t.uniforms[s]={type:"c",value:a.getHex()}:a&&a.isVector2?t.uniforms[s]={type:"v2",value:a.toArray()}:a&&a.isVector3?t.uniforms[s]={type:"v3",value:a.toArray()}:a&&a.isVector4?t.uniforms[s]={type:"v4",value:a.toArray()}:a&&a.isMatrix3?t.uniforms[s]={type:"m3",value:a.toArray()}:a&&a.isMatrix4?t.uniforms[s]={type:"m4",value:a.toArray()}:t.uniforms[s]={value:a}}Object.keys(this.defines).length>0&&(t.defines=this.defines),t.vertexShader=this.vertexShader,t.fragmentShader=this.fragmentShader,t.lights=this.lights,t.clipping=this.clipping;let n={};for(let s in this.extensions)this.extensions[s]===!0&&(n[s]=!0);return Object.keys(n).length>0&&(t.extensions=n),t}},Xi=class extends Gt{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new ut,this.projectionMatrix=new ut,this.projectionMatrixInverse=new ut,this.coordinateSystem=Zt,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,t){return super.copy(e,t),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorldInverse.copy(this.matrixWorld).invert()}updateWorldMatrix(e,t){super.updateWorldMatrix(e,t),this.matrixWorldInverse.copy(this.matrixWorld).invert()}clone(){return new this.constructor().copy(this)}},Cn=new F,$o=new Je,Ko=new Je,yt=class extends Xi{constructor(e=50,t=1,n=.1,s=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=n,this.far=s,this.focus=10,this.aspect=t,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){let t=.5*this.getFilmHeight()/e;this.fov=Os*2*Math.atan(t),this.updateProjectionMatrix()}getFocalLength(){let e=Math.tan(ca*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return Os*2*Math.atan(Math.tan(ca*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,t,n){Cn.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),t.set(Cn.x,Cn.y).multiplyScalar(-e/Cn.z),Cn.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),n.set(Cn.x,Cn.y).multiplyScalar(-e/Cn.z)}getViewSize(e,t){return this.getViewBounds(e,$o,Ko),t.subVectors(Ko,$o)}setViewOffset(e,t,n,s,r,a){this.aspect=e/t,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let e=this.near,t=e*Math.tan(ca*.5*this.fov)/this.zoom,n=2*t,s=this.aspect*n,r=-.5*s,a=this.view;if(this.view!==null&&this.view.enabled){let c=a.fullWidth,l=a.fullHeight;r+=a.offsetX*s/c,t-=a.offsetY*n/l,s*=a.width/c,n*=a.height/l}let o=this.filmOffset;o!==0&&(r+=e*o/this.getFilmWidth()),this.projectionMatrix.makePerspective(r,r+s,t,t-n,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);return t.object.fov=this.fov,t.object.zoom=this.zoom,t.object.near=this.near,t.object.far=this.far,t.object.focus=this.focus,t.object.aspect=this.aspect,this.view!==null&&(t.object.view=Object.assign({},this.view)),t.object.filmGauge=this.filmGauge,t.object.filmOffset=this.filmOffset,t}},gi=-90,_i=1,Gs=class extends Gt{constructor(e,t,n){super(),this.type="CubeCamera",this.renderTarget=n,this.coordinateSystem=null,this.activeMipmapLevel=0;let s=new yt(gi,_i,e,t);s.layers=this.layers,this.add(s);let r=new yt(gi,_i,e,t);r.layers=this.layers,this.add(r);let a=new yt(gi,_i,e,t);a.layers=this.layers,this.add(a);let o=new yt(gi,_i,e,t);o.layers=this.layers,this.add(o);let c=new yt(gi,_i,e,t);c.layers=this.layers,this.add(c);let l=new yt(gi,_i,e,t);l.layers=this.layers,this.add(l)}updateCoordinateSystem(){let e=this.coordinateSystem,t=this.children.concat(),[n,s,r,a,o,c]=t;for(let l of t)this.remove(l);if(e===Zt)n.up.set(0,1,0),n.lookAt(1,0,0),s.up.set(0,1,0),s.lookAt(-1,0,0),r.up.set(0,0,-1),r.lookAt(0,1,0),a.up.set(0,0,1),a.lookAt(0,-1,0),o.up.set(0,1,0),o.lookAt(0,0,1),c.up.set(0,1,0),c.lookAt(0,0,-1);else if(e===zi)n.up.set(0,-1,0),n.lookAt(-1,0,0),s.up.set(0,-1,0),s.lookAt(1,0,0),r.up.set(0,0,1),r.lookAt(0,1,0),a.up.set(0,0,-1),a.lookAt(0,-1,0),o.up.set(0,-1,0),o.lookAt(0,0,1),c.up.set(0,-1,0),c.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(let l of t)this.add(l),l.updateMatrixWorld()}update(e,t){this.parent===null&&this.updateMatrixWorld();let{renderTarget:n,activeMipmapLevel:s}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());let[r,a,o,c,l,h]=this.children,f=e.getRenderTarget(),p=e.getActiveCubeFace(),d=e.getActiveMipmapLevel(),_=e.xr.enabled;e.xr.enabled=!1;let y=n.texture.generateMipmaps;n.texture.generateMipmaps=!1,e.setRenderTarget(n,0,s),e.render(t,r),e.setRenderTarget(n,1,s),e.render(t,a),e.setRenderTarget(n,2,s),e.render(t,o),e.setRenderTarget(n,3,s),e.render(t,c),e.setRenderTarget(n,4,s),e.render(t,l),n.texture.generateMipmaps=y,e.setRenderTarget(n,5,s),e.render(t,h),e.setRenderTarget(f,p,d),e.xr.enabled=_,n.texture.needsPMREMUpdate=!0}},qi=class extends At{constructor(e=[],t=Nn,n,s,r,a,o,c,l,h){super(e,t,n,s,r,a,o,c,l,h),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}},Yi=class extends Nt{constructor(e=1,t={}){super(e,e,t),this.isWebGLCubeRenderTarget=!0;let n={width:e,height:e,depth:1},s=[n,n,n,n,n,n];this.texture=new qi(s),this._setTextureOptions(t),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,t){this.texture.type=t.type,this.texture.colorSpace=t.colorSpace,this.texture.generateMipmaps=t.generateMipmaps,this.texture.minFilter=t.minFilter,this.texture.magFilter=t.magFilter;let n={uniforms:{tEquirect:{value:null}},vertexShader:`

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,fragmentShader:`

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`},s=new bi(5,5,5),r=new Ft({name:"CubemapFromEquirect",uniforms:ti(n.uniforms),vertexShader:n.vertexShader,fragmentShader:n.fragmentShader,side:Tt,blending:an});r.uniforms.tEquirect.value=t;let a=new Rt(s,r),o=t.minFilter;return t.minFilter===Fn&&(t.minFilter=_t),new Gs(1,10,this).update(e,a),t.minFilter=o,a.geometry.dispose(),a.material.dispose(),this}clear(e,t=!0,n=!0,s=!0){let r=e.getRenderTarget();for(let a=0;a<6;a++)e.setRenderTarget(this,a),e.clear(t,n,s);e.setRenderTarget(r)}},gn=class extends Gt{constructor(){super(),this.isGroup=!0,this.type="Group"}},Fc={type:"move"},Ai=class{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new gn,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new gn,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new F,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new F),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new gn,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new F,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new F),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){let t=this._hand;if(t)for(let n of e.hand.values())this._getHandJoint(t,n)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,t,n){let s=null,r=null,a=null,o=this._targetRay,c=this._grip,l=this._hand;if(e&&t.session.visibilityState!=="visible-blurred"){if(l&&e.hand){a=!0;for(let y of e.hand.values()){let m=t.getJointPose(y,n),u=this._getHandJoint(l,y);m!==null&&(u.matrix.fromArray(m.transform.matrix),u.matrix.decompose(u.position,u.rotation,u.scale),u.matrixWorldNeedsUpdate=!0,u.jointRadius=m.radius),u.visible=m!==null}let h=l.joints["index-finger-tip"],f=l.joints["thumb-tip"],p=h.position.distanceTo(f.position),d=.02,_=.005;l.inputState.pinching&&p>d+_?(l.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!l.inputState.pinching&&p<=d-_&&(l.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else c!==null&&e.gripSpace&&(r=t.getPose(e.gripSpace,n),r!==null&&(c.matrix.fromArray(r.transform.matrix),c.matrix.decompose(c.position,c.rotation,c.scale),c.matrixWorldNeedsUpdate=!0,r.linearVelocity?(c.hasLinearVelocity=!0,c.linearVelocity.copy(r.linearVelocity)):c.hasLinearVelocity=!1,r.angularVelocity?(c.hasAngularVelocity=!0,c.angularVelocity.copy(r.angularVelocity)):c.hasAngularVelocity=!1));o!==null&&(s=t.getPose(e.targetRaySpace,n),s===null&&r!==null&&(s=r),s!==null&&(o.matrix.fromArray(s.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,s.linearVelocity?(o.hasLinearVelocity=!0,o.linearVelocity.copy(s.linearVelocity)):o.hasLinearVelocity=!1,s.angularVelocity?(o.hasAngularVelocity=!0,o.angularVelocity.copy(s.angularVelocity)):o.hasAngularVelocity=!1,this.dispatchEvent(Fc)))}return o!==null&&(o.visible=s!==null),c!==null&&(c.visible=r!==null),l!==null&&(l.visible=a!==null),this}_getHandJoint(e,t){if(e.joints[t.jointName]===void 0){let n=new gn;n.matrixAutoUpdate=!1,n.visible=!1,e.joints[t.jointName]=n,e.add(n)}return e.joints[t.jointName]}};var Zi=class extends Gt{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new nn,this.environmentIntensity=1,this.environmentRotation=new nn,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,t){return super.copy(e,t),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){let t=super.toJSON(e);return this.fog!==null&&(t.object.fog=this.fog.toJSON()),this.backgroundBlurriness>0&&(t.object.backgroundBlurriness=this.backgroundBlurriness),this.backgroundIntensity!==1&&(t.object.backgroundIntensity=this.backgroundIntensity),t.object.backgroundRotation=this.backgroundRotation.toArray(),this.environmentIntensity!==1&&(t.object.environmentIntensity=this.environmentIntensity),t.object.environmentRotation=this.environmentRotation.toArray(),t}};var Hs=class extends At{constructor(e=null,t=1,n=1,s,r,a,o,c,l=gt,h=gt,f,p){super(null,a,o,c,l,h,s,r,f,p),this.isDataTexture=!0,this.image={data:e,width:t,height:n},this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}};var Pa=new F,Oc=new F,Bc=new Ie,jt=class{constructor(e=new F(1,0,0),t=0){this.isPlane=!0,this.normal=e,this.constant=t}set(e,t){return this.normal.copy(e),this.constant=t,this}setComponents(e,t,n,s){return this.normal.set(e,t,n),this.constant=s,this}setFromNormalAndCoplanarPoint(e,t){return this.normal.copy(e),this.constant=-t.dot(this.normal),this}setFromCoplanarPoints(e,t,n){let s=Pa.subVectors(n,t).cross(Oc.subVectors(e,t)).normalize();return this.setFromNormalAndCoplanarPoint(s,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){let e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,t){return t.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,t){let n=e.delta(Pa),s=this.normal.dot(n);if(s===0)return this.distanceToPoint(e.start)===0?t.copy(e.start):null;let r=-(e.start.dot(this.normal)+this.constant)/s;return r<0||r>1?null:t.copy(e.start).addScaledVector(n,r)}intersectsLine(e){let t=this.distanceToPoint(e.start),n=this.distanceToPoint(e.end);return t<0&&n>0||n<0&&t>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,t){let n=t||Bc.getNormalMatrix(e),s=this.coplanarPoint(Pa).applyMatrix4(e),r=this.normal.applyMatrix3(n).normalize();return this.constant=-s.dot(r),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}},Wn=new Si,zc=new Je(.5,.5),Rs=new F,Ji=class{constructor(e=new jt,t=new jt,n=new jt,s=new jt,r=new jt,a=new jt){this.planes=[e,t,n,s,r,a]}set(e,t,n,s,r,a){let o=this.planes;return o[0].copy(e),o[1].copy(t),o[2].copy(n),o[3].copy(s),o[4].copy(r),o[5].copy(a),this}copy(e){let t=this.planes;for(let n=0;n<6;n++)t[n].copy(e.planes[n]);return this}setFromProjectionMatrix(e,t=Zt,n=!1){let s=this.planes,r=e.elements,a=r[0],o=r[1],c=r[2],l=r[3],h=r[4],f=r[5],p=r[6],d=r[7],_=r[8],y=r[9],m=r[10],u=r[11],b=r[12],T=r[13],A=r[14],E=r[15];if(s[0].setComponents(l-a,d-h,u-_,E-b).normalize(),s[1].setComponents(l+a,d+h,u+_,E+b).normalize(),s[2].setComponents(l+o,d+f,u+y,E+T).normalize(),s[3].setComponents(l-o,d-f,u-y,E-T).normalize(),n)s[4].setComponents(c,p,m,A).normalize(),s[5].setComponents(l-c,d-p,u-m,E-A).normalize();else if(s[4].setComponents(l-c,d-p,u-m,E-A).normalize(),t===Zt)s[5].setComponents(l+c,d+p,u+m,E+A).normalize();else if(t===zi)s[5].setComponents(c,p,m,A).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+t);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),Wn.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{let t=e.geometry;t.boundingSphere===null&&t.computeBoundingSphere(),Wn.copy(t.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(Wn)}intersectsSprite(e){Wn.center.set(0,0,0);let t=zc.distanceTo(e.center);return Wn.radius=.7071067811865476+t,Wn.applyMatrix4(e.matrixWorld),this.intersectsSphere(Wn)}intersectsSphere(e){let t=this.planes,n=e.center,s=-e.radius;for(let r=0;r<6;r++)if(t[r].distanceToPoint(n)<s)return!1;return!0}intersectsBox(e){let t=this.planes;for(let n=0;n<6;n++){let s=t[n];if(Rs.x=s.normal.x>0?e.max.x:e.min.x,Rs.y=s.normal.y>0?e.max.y:e.min.y,Rs.z=s.normal.z>0?e.max.z:e.min.z,s.distanceToPoint(Rs)<0)return!1}return!0}containsPoint(e){let t=this.planes;for(let n=0;n<6;n++)if(t[n].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}};var $i=class extends At{constructor(e,t,n,s,r,a,o,c,l){super(e,t,n,s,r,a,o,c,l),this.isCanvasTexture=!0,this.needsUpdate=!0}},Ln=class extends At{constructor(e,t,n=$t,s,r,a,o=gt,c=gt,l,h=tn,f=1){if(h!==tn&&h!==On)throw new Error("DepthTexture format must be either THREE.DepthFormat or THREE.DepthStencilFormat");let p={width:e,height:t,depth:f};super(p,s,r,a,o,c,h,n,l),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new Mi(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){let t=super.toJSON(e);return this.compareFunction!==null&&(t.compareFunction=this.compareFunction),t}},Ws=class extends Ln{constructor(e,t=$t,n=Nn,s,r,a=gt,o=gt,c,l=tn){let h={width:e,height:e,depth:1},f=[h,h,h,h,h,h];super(e,e,t,n,s,r,a,o,c,l),this.image=f,this.isCubeDepthTexture=!0,this.isCubeTexture=!0}get images(){return this.image}set images(e){this.image=e}},Ki=class extends At{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}};var Kn=class i extends sn{constructor(e=1,t=1,n=1,s=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:t,widthSegments:n,heightSegments:s};let r=e/2,a=t/2,o=Math.floor(n),c=Math.floor(s),l=o+1,h=c+1,f=e/o,p=t/c,d=[],_=[],y=[],m=[];for(let u=0;u<h;u++){let b=u*p-a;for(let T=0;T<l;T++){let A=T*f-r;_.push(A,-b,0),y.push(0,0,1),m.push(T/o),m.push(1-u/c)}}for(let u=0;u<c;u++)for(let b=0;b<o;b++){let T=b+l*u,A=b+l*(u+1),E=b+1+l*(u+1),w=b+1+l*u;d.push(T,A,w),d.push(A,E,w)}this.setIndex(d),this.setAttribute("position",new kt(_,3)),this.setAttribute("normal",new kt(y,3)),this.setAttribute("uv",new kt(m,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.width,e.height,e.widthSegments,e.heightSegments)}};var Xs=class extends Ft{constructor(e){super(e),this.isRawShaderMaterial=!0,this.type="RawShaderMaterial"}};var qs=class extends Jn{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=Sl,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}},Ys=class extends Jn{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}};function Is(i,e){return!i||i.constructor===e?i:typeof e.BYTES_PER_ELEMENT=="number"?new e(i):Array.prototype.slice.call(i)}var Qn=class{constructor(e,t,n,s){this.parameterPositions=e,this._cachedIndex=0,this.resultBuffer=s!==void 0?s:new t.constructor(n),this.sampleValues=t,this.valueSize=n,this.settings=null,this.DefaultSettings_={}}evaluate(e){let t=this.parameterPositions,n=this._cachedIndex,s=t[n],r=t[n-1];n:{e:{let a;t:{i:if(!(e<s)){for(let o=n+2;;){if(s===void 0){if(e<r)break i;return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}if(n===o)break;if(r=s,s=t[++n],e<s)break e}a=t.length;break t}if(!(e>=r)){let o=t[1];e<o&&(n=2,r=o);for(let c=n-2;;){if(r===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(n===c)break;if(s=r,r=t[--n-1],e>=r)break e}a=n,n=0;break t}break n}for(;n<a;){let o=n+a>>>1;e<t[o]?a=o:n=o+1}if(s=t[n],r=t[n-1],r===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(s===void 0)return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}this._cachedIndex=n,this.intervalChanged_(n,r,s)}return this.interpolate_(n,r,e,s)}getSettings_(){return this.settings||this.DefaultSettings_}copySampleValue_(e){let t=this.resultBuffer,n=this.sampleValues,s=this.valueSize,r=e*s;for(let a=0;a!==s;++a)t[a]=n[r+a];return t}interpolate_(){throw new Error("call to abstract method")}intervalChanged_(){}},Zs=class extends Qn{constructor(e,t,n,s){super(e,t,n,s),this._weightPrev=-0,this._offsetPrev=-0,this._weightNext=-0,this._offsetNext=-0,this.DefaultSettings_={endingStart:La,endingEnd:La}}intervalChanged_(e,t,n){let s=this.parameterPositions,r=e-2,a=e+1,o=s[r],c=s[a];if(o===void 0)switch(this.getSettings_().endingStart){case Da:r=e,o=2*t-n;break;case Ua:r=s.length-2,o=t+s[r]-s[r+1];break;default:r=e,o=n}if(c===void 0)switch(this.getSettings_().endingEnd){case Da:a=e,c=2*n-t;break;case Ua:a=1,c=n+s[1]-s[0];break;default:a=e-1,c=t}let l=(n-t)*.5,h=this.valueSize;this._weightPrev=l/(t-o),this._weightNext=l/(c-n),this._offsetPrev=r*h,this._offsetNext=a*h}interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=e*o,l=c-o,h=this._offsetPrev,f=this._offsetNext,p=this._weightPrev,d=this._weightNext,_=(n-t)/(s-t),y=_*_,m=y*_,u=-p*m+2*p*y-p*_,b=(1+p)*m+(-1.5-2*p)*y+(-.5+p)*_+1,T=(-1-d)*m+(1.5+d)*y+.5*_,A=d*m-d*y;for(let E=0;E!==o;++E)r[E]=u*a[h+E]+b*a[l+E]+T*a[c+E]+A*a[f+E];return r}},Js=class extends Qn{constructor(e,t,n,s){super(e,t,n,s)}interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=e*o,l=c-o,h=(n-t)/(s-t),f=1-h;for(let p=0;p!==o;++p)r[p]=a[l+p]*f+a[c+p]*h;return r}},$s=class extends Qn{constructor(e,t,n,s){super(e,t,n,s)}interpolate_(e){return this.copySampleValue_(e-1)}},Ot=class{constructor(e,t,n,s){if(e===void 0)throw new Error("THREE.KeyframeTrack: track name is undefined");if(t===void 0||t.length===0)throw new Error("THREE.KeyframeTrack: no keyframes in track named "+e);this.name=e,this.times=Is(t,this.TimeBufferType),this.values=Is(n,this.ValueBufferType),this.setInterpolation(s||this.DefaultInterpolation)}static toJSON(e){let t=e.constructor,n;if(t.toJSON!==this.toJSON)n=t.toJSON(e);else{n={name:e.name,times:Is(e.times,Array),values:Is(e.values,Array)};let s=e.getInterpolation();s!==e.DefaultInterpolation&&(n.interpolation=s)}return n.type=e.ValueTypeName,n}InterpolantFactoryMethodDiscrete(e){return new $s(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodLinear(e){return new Js(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodSmooth(e){return new Zs(this.times,this.values,this.getValueSize(),e)}setInterpolation(e){let t;switch(e){case Oi:t=this.InterpolantFactoryMethodDiscrete;break;case Fs:t=this.InterpolantFactoryMethodLinear;break;case Ps:t=this.InterpolantFactoryMethodSmooth;break}if(t===void 0){let n="unsupported interpolation for "+this.ValueTypeName+" keyframe track named "+this.name;if(this.createInterpolant===void 0)if(e!==this.DefaultInterpolation)this.setInterpolation(this.DefaultInterpolation);else throw new Error(n);return Ce("KeyframeTrack:",n),this}return this.createInterpolant=t,this}getInterpolation(){switch(this.createInterpolant){case this.InterpolantFactoryMethodDiscrete:return Oi;case this.InterpolantFactoryMethodLinear:return Fs;case this.InterpolantFactoryMethodSmooth:return Ps}}getValueSize(){return this.values.length/this.times.length}shift(e){if(e!==0){let t=this.times;for(let n=0,s=t.length;n!==s;++n)t[n]+=e}return this}scale(e){if(e!==1){let t=this.times;for(let n=0,s=t.length;n!==s;++n)t[n]*=e}return this}trim(e,t){let n=this.times,s=n.length,r=0,a=s-1;for(;r!==s&&n[r]<e;)++r;for(;a!==-1&&n[a]>t;)--a;if(++a,r!==0||a!==s){r>=a&&(a=Math.max(a,1),r=a-1);let o=this.getValueSize();this.times=n.slice(r,a),this.values=this.values.slice(r*o,a*o)}return this}validate(){let e=!0,t=this.getValueSize();t-Math.floor(t)!==0&&(Ee("KeyframeTrack: Invalid value size in track.",this),e=!1);let n=this.times,s=this.values,r=n.length;r===0&&(Ee("KeyframeTrack: Track is empty.",this),e=!1);let a=null;for(let o=0;o!==r;o++){let c=n[o];if(typeof c=="number"&&isNaN(c)){Ee("KeyframeTrack: Time is not a valid number.",this,o,c),e=!1;break}if(a!==null&&a>c){Ee("KeyframeTrack: Out of order keys.",this,o,c,a),e=!1;break}a=c}if(s!==void 0&&_c(s))for(let o=0,c=s.length;o!==c;++o){let l=s[o];if(isNaN(l)){Ee("KeyframeTrack: Value is not a valid number.",this,o,l),e=!1;break}}return e}optimize(){let e=this.times.slice(),t=this.values.slice(),n=this.getValueSize(),s=this.getInterpolation()===Ps,r=e.length-1,a=1;for(let o=1;o<r;++o){let c=!1,l=e[o],h=e[o+1];if(l!==h&&(o!==1||l!==e[0]))if(s)c=!0;else{let f=o*n,p=f-n,d=f+n;for(let _=0;_!==n;++_){let y=t[f+_];if(y!==t[p+_]||y!==t[d+_]){c=!0;break}}}if(c){if(o!==a){e[a]=e[o];let f=o*n,p=a*n;for(let d=0;d!==n;++d)t[p+d]=t[f+d]}++a}}if(r>0){e[a]=e[r];for(let o=r*n,c=a*n,l=0;l!==n;++l)t[c+l]=t[o+l];++a}return a!==e.length?(this.times=e.slice(0,a),this.values=t.slice(0,a*n)):(this.times=e,this.values=t),this}clone(){let e=this.times.slice(),t=this.values.slice(),n=this.constructor,s=new n(this.name,e,t);return s.createInterpolant=this.createInterpolant,s}};Ot.prototype.ValueTypeName="";Ot.prototype.TimeBufferType=Float32Array;Ot.prototype.ValueBufferType=Float32Array;Ot.prototype.DefaultInterpolation=Fs;var Dn=class extends Ot{constructor(e,t,n){super(e,t,n)}};Dn.prototype.ValueTypeName="bool";Dn.prototype.ValueBufferType=Array;Dn.prototype.DefaultInterpolation=Oi;Dn.prototype.InterpolantFactoryMethodLinear=void 0;Dn.prototype.InterpolantFactoryMethodSmooth=void 0;var Ks=class extends Ot{constructor(e,t,n,s){super(e,t,n,s)}};Ks.prototype.ValueTypeName="color";var Qs=class extends Ot{constructor(e,t,n,s){super(e,t,n,s)}};Qs.prototype.ValueTypeName="number";var js=class extends Qn{constructor(e,t,n,s){super(e,t,n,s)}interpolate_(e,t,n,s){let r=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=(n-t)/(s-t),l=e*o;for(let h=l+o;l!==h;l+=4)yn.slerpFlat(r,0,a,l-o,a,l,c);return r}},Qi=class extends Ot{constructor(e,t,n,s){super(e,t,n,s)}InterpolantFactoryMethodLinear(e){return new js(this.times,this.values,this.getValueSize(),e)}};Qi.prototype.ValueTypeName="quaternion";Qi.prototype.InterpolantFactoryMethodSmooth=void 0;var Un=class extends Ot{constructor(e,t,n){super(e,t,n)}};Un.prototype.ValueTypeName="string";Un.prototype.ValueBufferType=Array;Un.prototype.DefaultInterpolation=Oi;Un.prototype.InterpolantFactoryMethodLinear=void 0;Un.prototype.InterpolantFactoryMethodSmooth=void 0;var er=class extends Ot{constructor(e,t,n,s){super(e,t,n,s)}};er.prototype.ValueTypeName="vector";var tr=class{constructor(e,t,n){let s=this,r=!1,a=0,o=0,c,l=[];this.onStart=void 0,this.onLoad=e,this.onProgress=t,this.onError=n,this._abortController=null,this.itemStart=function(h){o++,r===!1&&s.onStart!==void 0&&s.onStart(h,a,o),r=!0},this.itemEnd=function(h){a++,s.onProgress!==void 0&&s.onProgress(h,a,o),a===o&&(r=!1,s.onLoad!==void 0&&s.onLoad())},this.itemError=function(h){s.onError!==void 0&&s.onError(h)},this.resolveURL=function(h){return c?c(h):h},this.setURLModifier=function(h){return c=h,this},this.addHandler=function(h,f){return l.push(h,f),this},this.removeHandler=function(h){let f=l.indexOf(h);return f!==-1&&l.splice(f,2),this},this.getHandler=function(h){for(let f=0,p=l.length;f<p;f+=2){let d=l[f],_=l[f+1];if(d.global&&(d.lastIndex=0),d.test(h))return _}return null},this.abort=function(){return this.abortController.abort(),this._abortController=null,this}}get abortController(){return this._abortController||(this._abortController=new AbortController),this._abortController}},Nl=new tr,nr=class{constructor(e){this.manager=e!==void 0?e:Nl,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={}}load(){}loadAsync(e,t){let n=this;return new Promise(function(s,r){n.load(e,s,t,r)})}parse(){}setCrossOrigin(e){return this.crossOrigin=e,this}setWithCredentials(e){return this.withCredentials=e,this}setPath(e){return this.path=e,this}setResourcePath(e){return this.resourcePath=e,this}setRequestHeader(e){return this.requestHeader=e,this}abort(){return this}};nr.DEFAULT_MATERIAL_NAME="__DEFAULT";var ji=class extends Xi{constructor(e=-1,t=1,n=1,s=-1,r=.1,a=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=t,this.top=n,this.bottom=s,this.near=r,this.far=a,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,t,n,s,r,a){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=s,this.view.width=r,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let e=(this.right-this.left)/(2*this.zoom),t=(this.top-this.bottom)/(2*this.zoom),n=(this.right+this.left)/2,s=(this.top+this.bottom)/2,r=n-e,a=n+e,o=s+t,c=s-t;if(this.view!==null&&this.view.enabled){let l=(this.right-this.left)/this.view.fullWidth/this.zoom,h=(this.top-this.bottom)/this.view.fullHeight/this.zoom;r+=l*this.view.offsetX,a=r+l*this.view.width,o-=h*this.view.offsetY,c=o-h*this.view.height}this.projectionMatrix.makeOrthographic(r,a,o,c,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);return t.object.zoom=this.zoom,t.object.left=this.left,t.object.right=this.right,t.object.top=this.top,t.object.bottom=this.bottom,t.object.near=this.near,t.object.far=this.far,this.view!==null&&(t.object.view=Object.assign({},this.view)),t}};var ir=class extends yt{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}};var lo="\\[\\]\\.:\\/",Vc=new RegExp("["+lo+"]","g"),co="[^"+lo+"]",kc="[^"+lo.replace("\\.","")+"]",Gc=/((?:WC+[\/:])*)/.source.replace("WC",co),Hc=/(WCOD+)?/.source.replace("WCOD",kc),Wc=/(?:\.(WC+)(?:\[(.+)\])?)?/.source.replace("WC",co),Xc=/\.(WC+)(?:\[(.+)\])?/.source.replace("WC",co),qc=new RegExp("^"+Gc+Hc+Wc+Xc+"$"),Yc=["material","materials","bones","map"],Oa=class{constructor(e,t,n){let s=n||it.parseTrackName(t);this._targetGroup=e,this._bindings=e.subscribe_(t,s)}getValue(e,t){this.bind();let n=this._targetGroup.nCachedObjects_,s=this._bindings[n];s!==void 0&&s.getValue(e,t)}setValue(e,t){let n=this._bindings;for(let s=this._targetGroup.nCachedObjects_,r=n.length;s!==r;++s)n[s].setValue(e,t)}bind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].bind()}unbind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].unbind()}},it=class i{constructor(e,t,n){this.path=t,this.parsedPath=n||i.parseTrackName(t),this.node=i.findNode(e,this.parsedPath.nodeName),this.rootNode=e,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}static create(e,t,n){return e&&e.isAnimationObjectGroup?new i.Composite(e,t,n):new i(e,t,n)}static sanitizeNodeName(e){return e.replace(/\s/g,"_").replace(Vc,"")}static parseTrackName(e){let t=qc.exec(e);if(t===null)throw new Error("PropertyBinding: Cannot parse trackName: "+e);let n={nodeName:t[2],objectName:t[3],objectIndex:t[4],propertyName:t[5],propertyIndex:t[6]},s=n.nodeName&&n.nodeName.lastIndexOf(".");if(s!==void 0&&s!==-1){let r=n.nodeName.substring(s+1);Yc.indexOf(r)!==-1&&(n.nodeName=n.nodeName.substring(0,s),n.objectName=r)}if(n.propertyName===null||n.propertyName.length===0)throw new Error("PropertyBinding: can not parse propertyName from trackName: "+e);return n}static findNode(e,t){if(t===void 0||t===""||t==="."||t===-1||t===e.name||t===e.uuid)return e;if(e.skeleton){let n=e.skeleton.getBoneByName(t);if(n!==void 0)return n}if(e.children){let n=function(r){for(let a=0;a<r.length;a++){let o=r[a];if(o.name===t||o.uuid===t)return o;let c=n(o.children);if(c)return c}return null},s=n(e.children);if(s)return s}return null}_getValue_unavailable(){}_setValue_unavailable(){}_getValue_direct(e,t){e[t]=this.targetObject[this.propertyName]}_getValue_array(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)e[t++]=n[s]}_getValue_arrayElement(e,t){e[t]=this.resolvedProperty[this.propertyIndex]}_getValue_toArray(e,t){this.resolvedProperty.toArray(e,t)}_setValue_direct(e,t){this.targetObject[this.propertyName]=e[t]}_setValue_direct_setNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.needsUpdate=!0}_setValue_direct_setMatrixWorldNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_array(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=e[t++]}_setValue_array_setNeedsUpdate(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=e[t++];this.targetObject.needsUpdate=!0}_setValue_array_setMatrixWorldNeedsUpdate(e,t){let n=this.resolvedProperty;for(let s=0,r=n.length;s!==r;++s)n[s]=e[t++];this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_arrayElement(e,t){this.resolvedProperty[this.propertyIndex]=e[t]}_setValue_arrayElement_setNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.needsUpdate=!0}_setValue_arrayElement_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_fromArray(e,t){this.resolvedProperty.fromArray(e,t)}_setValue_fromArray_setNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.needsUpdate=!0}_setValue_fromArray_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.matrixWorldNeedsUpdate=!0}_getValue_unbound(e,t){this.bind(),this.getValue(e,t)}_setValue_unbound(e,t){this.bind(),this.setValue(e,t)}bind(){let e=this.node,t=this.parsedPath,n=t.objectName,s=t.propertyName,r=t.propertyIndex;if(e||(e=i.findNode(this.rootNode,t.nodeName),this.node=e),this.getValue=this._getValue_unavailable,this.setValue=this._setValue_unavailable,!e){Ce("PropertyBinding: No target node found for track: "+this.path+".");return}if(n){let l=t.objectIndex;switch(n){case"materials":if(!e.material){Ee("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.materials){Ee("PropertyBinding: Can not bind to material.materials as node.material does not have a materials array.",this);return}e=e.material.materials;break;case"bones":if(!e.skeleton){Ee("PropertyBinding: Can not bind to bones as node does not have a skeleton.",this);return}e=e.skeleton.bones;for(let h=0;h<e.length;h++)if(e[h].name===l){l=h;break}break;case"map":if("map"in e){e=e.map;break}if(!e.material){Ee("PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.map){Ee("PropertyBinding: Can not bind to material.map as node.material does not have a map.",this);return}e=e.material.map;break;default:if(e[n]===void 0){Ee("PropertyBinding: Can not bind to objectName of node undefined.",this);return}e=e[n]}if(l!==void 0){if(e[l]===void 0){Ee("PropertyBinding: Trying to bind to objectIndex of objectName, but is undefined.",this,e);return}e=e[l]}}let a=e[s];if(a===void 0){let l=t.nodeName;Ee("PropertyBinding: Trying to update property for track: "+l+"."+s+" but it wasn't found.",e);return}let o=this.Versioning.None;this.targetObject=e,e.isMaterial===!0?o=this.Versioning.NeedsUpdate:e.isObject3D===!0&&(o=this.Versioning.MatrixWorldNeedsUpdate);let c=this.BindingType.Direct;if(r!==void 0){if(s==="morphTargetInfluences"){if(!e.geometry){Ee("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.",this);return}if(!e.geometry.morphAttributes){Ee("PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.morphAttributes.",this);return}e.morphTargetDictionary[r]!==void 0&&(r=e.morphTargetDictionary[r])}c=this.BindingType.ArrayElement,this.resolvedProperty=a,this.propertyIndex=r}else a.fromArray!==void 0&&a.toArray!==void 0?(c=this.BindingType.HasFromToArray,this.resolvedProperty=a):Array.isArray(a)?(c=this.BindingType.EntireArray,this.resolvedProperty=a):this.propertyName=s;this.getValue=this.GetterByBindingType[c],this.setValue=this.SetterByBindingTypeAndVersioning[c][o]}unbind(){this.node=null,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}};it.Composite=Oa;it.prototype.BindingType={Direct:0,EntireArray:1,ArrayElement:2,HasFromToArray:3};it.prototype.Versioning={None:0,NeedsUpdate:1,MatrixWorldNeedsUpdate:2};it.prototype.GetterByBindingType=[it.prototype._getValue_direct,it.prototype._getValue_array,it.prototype._getValue_arrayElement,it.prototype._getValue_toArray];it.prototype.SetterByBindingTypeAndVersioning=[[it.prototype._setValue_direct,it.prototype._setValue_direct_setNeedsUpdate,it.prototype._setValue_direct_setMatrixWorldNeedsUpdate],[it.prototype._setValue_array,it.prototype._setValue_array_setNeedsUpdate,it.prototype._setValue_array_setMatrixWorldNeedsUpdate],[it.prototype._setValue_arrayElement,it.prototype._setValue_arrayElement_setNeedsUpdate,it.prototype._setValue_arrayElement_setMatrixWorldNeedsUpdate],[it.prototype._setValue_fromArray,it.prototype._setValue_fromArray_setNeedsUpdate,it.prototype._setValue_fromArray_setMatrixWorldNeedsUpdate]];var zp=new Float32Array(1);function ho(i,e,t,n){let s=Zc(n);switch(t){case to:return i*e;case io:return i*e/s.components*s.byteLength;case _r:return i*e/s.components*s.byteLength;case ei:return i*e*2/s.components*s.byteLength;case xr:return i*e*2/s.components*s.byteLength;case no:return i*e*3/s.components*s.byteLength;case Ht:return i*e*4/s.components*s.byteLength;case vr:return i*e*4/s.components*s.byteLength;case is:case ss:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case rs:case as:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case Mr:case br:return Math.max(i,16)*Math.max(e,8)/4;case yr:case Sr:return Math.max(i,8)*Math.max(e,8)/2;case Ar:case Tr:case wr:case Cr:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case Er:case Rr:case Ir:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case Pr:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case Lr:return Math.floor((i+4)/5)*Math.floor((e+3)/4)*16;case Dr:return Math.floor((i+4)/5)*Math.floor((e+4)/5)*16;case Ur:return Math.floor((i+5)/6)*Math.floor((e+4)/5)*16;case Nr:return Math.floor((i+5)/6)*Math.floor((e+5)/6)*16;case Fr:return Math.floor((i+7)/8)*Math.floor((e+4)/5)*16;case Or:return Math.floor((i+7)/8)*Math.floor((e+5)/6)*16;case Br:return Math.floor((i+7)/8)*Math.floor((e+7)/8)*16;case zr:return Math.floor((i+9)/10)*Math.floor((e+4)/5)*16;case Vr:return Math.floor((i+9)/10)*Math.floor((e+5)/6)*16;case kr:return Math.floor((i+9)/10)*Math.floor((e+7)/8)*16;case Gr:return Math.floor((i+9)/10)*Math.floor((e+9)/10)*16;case Hr:return Math.floor((i+11)/12)*Math.floor((e+9)/10)*16;case Wr:return Math.floor((i+11)/12)*Math.floor((e+11)/12)*16;case Xr:case qr:case Yr:return Math.ceil(i/4)*Math.ceil(e/4)*16;case Zr:case Jr:return Math.ceil(i/4)*Math.ceil(e/4)*8;case $r:case Kr:return Math.ceil(i/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${t} format.`)}function Zc(i){switch(i){case Bt:case Ka:return{byteLength:1,components:1};case Ei:case Qa:case on:return{byteLength:2,components:1};case mr:case gr:return{byteLength:2,components:4};case $t:case pr:case Kt:return{byteLength:4,components:1};case ja:case eo:return{byteLength:4,components:3}}throw new Error(`Unknown texture type ${i}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:"182"}}));typeof window<"u"&&(window.__THREE__?Ce("WARNING: Multiple instances of Three.js being imported."):window.__THREE__="182");function sc(){let i=null,e=!1,t=null,n=null;function s(r,a){t(r,a),n=i.requestAnimationFrame(s)}return{start:function(){e!==!0&&t!==null&&(n=i.requestAnimationFrame(s),e=!0)},stop:function(){i.cancelAnimationFrame(n),e=!1},setAnimationLoop:function(r){t=r},setContext:function(r){i=r}}}function $c(i){let e=new WeakMap;function t(o,c){let l=o.array,h=o.usage,f=l.byteLength,p=i.createBuffer();i.bindBuffer(c,p),i.bufferData(c,l,h),o.onUploadCallback();let d;if(l instanceof Float32Array)d=i.FLOAT;else if(typeof Float16Array<"u"&&l instanceof Float16Array)d=i.HALF_FLOAT;else if(l instanceof Uint16Array)o.isFloat16BufferAttribute?d=i.HALF_FLOAT:d=i.UNSIGNED_SHORT;else if(l instanceof Int16Array)d=i.SHORT;else if(l instanceof Uint32Array)d=i.UNSIGNED_INT;else if(l instanceof Int32Array)d=i.INT;else if(l instanceof Int8Array)d=i.BYTE;else if(l instanceof Uint8Array)d=i.UNSIGNED_BYTE;else if(l instanceof Uint8ClampedArray)d=i.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+l);return{buffer:p,type:d,bytesPerElement:l.BYTES_PER_ELEMENT,version:o.version,size:f}}function n(o,c,l){let h=c.array,f=c.updateRanges;if(i.bindBuffer(l,o),f.length===0)i.bufferSubData(l,0,h);else{f.sort((d,_)=>d.start-_.start);let p=0;for(let d=1;d<f.length;d++){let _=f[p],y=f[d];y.start<=_.start+_.count+1?_.count=Math.max(_.count,y.start+y.count-_.start):(++p,f[p]=y)}f.length=p+1;for(let d=0,_=f.length;d<_;d++){let y=f[d];i.bufferSubData(l,y.start*h.BYTES_PER_ELEMENT,h,y.start,y.count)}c.clearUpdateRanges()}c.onUploadCallback()}function s(o){return o.isInterleavedBufferAttribute&&(o=o.data),e.get(o)}function r(o){o.isInterleavedBufferAttribute&&(o=o.data);let c=e.get(o);c&&(i.deleteBuffer(c.buffer),e.delete(o))}function a(o,c){if(o.isInterleavedBufferAttribute&&(o=o.data),o.isGLBufferAttribute){let h=e.get(o);(!h||h.version<o.version)&&e.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}let l=e.get(o);if(l===void 0)e.set(o,t(o,c));else if(l.version<o.version){if(l.size!==o.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");n(l.buffer,o,c),l.version=o.version}}return{get:s,remove:r,update:a}}var Kc=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,Qc=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,jc=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,eh=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,th=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,nh=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,ih=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT ) 
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN ) 
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,sh=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,rh=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec3 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 ).rgb;
	}
#endif`,ah=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,oh=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,lh=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,ch=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,hh=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,uh=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,dh=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,fh=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,ph=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,mh=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,gh=`#if defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#elif defined( USE_COLOR )
	diffuseColor.rgb *= vColor;
#endif`,_h=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR )
	varying vec3 vColor;
#endif`,xh=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec3 vColor;
#endif`,vh=`#if defined( USE_COLOR_ALPHA )
	vColor = vec4( 1.0 );
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec3( 1.0 );
#endif
#ifdef USE_COLOR
	vColor *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.xyz *= instanceColor.xyz;
#endif
#ifdef USE_BATCHING_COLOR
	vec3 batchingColor = getBatchingColor( getIndirectIndex( gl_DrawID ) );
	vColor.xyz *= batchingColor.xyz;
#endif`,yh=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
vec3 inverseTransformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( vec4( dir, 0.0 ) * matrix ).xyz );
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,Mh=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,Sh=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
	#ifdef FLIP_SIDED
		transformedTangent = - transformedTangent;
	#endif
#endif`,bh=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,Ah=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,Th=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,Eh=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,wh="gl_FragColor = linearToOutputTexel( gl_FragColor );",Ch=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,Rh=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * vec3( flipEnvMap * reflectVec.x, reflectVec.yz ) );
	#else
		vec4 envColor = vec4( 0.0 );
	#endif
	#ifdef ENVMAP_BLENDING_MULTIPLY
		outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_MIX )
		outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_ADD )
		outgoingLight += envColor.xyz * specularStrength * reflectivity;
	#endif
#endif`,Ih=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform float flipEnvMap;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
#endif`,Ph=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,Lh=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,Dh=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,Uh=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,Nh=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,Fh=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,Oh=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,Bh=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,zh=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,Vh=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,kh=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,Gh=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif`,Hh=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, pow4( roughness ) ) );
			reflectVec = inverseTransformDirection( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
#endif`,Wh=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,Xh=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,qh=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,Yh=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,Zh=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.diffuseContribution = diffuseColor.rgb * ( 1.0 - metalnessFactor );
material.metalness = metalnessFactor;
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor;
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = vec3( 0.04 );
	material.specularColorBlended = mix( material.specularColor, diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.0001, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,Jh=`uniform sampler2D dfgLUT;
struct PhysicalMaterial {
	vec3 diffuseColor;
	vec3 diffuseContribution;
	vec3 specularColor;
	vec3 specularColorBlended;
	float roughness;
	float metalness;
	float specularF90;
	float dispersion;
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0;
		vec3 iridescenceFresnelDielectric;
		vec3 iridescenceFresnelMetallic;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		float v = 0.5 / ( gv + gl );
		return v;
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColorBlended;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transpose( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float rInv = 1.0 / ( roughness + 0.1 );
	float a = -1.9362 + 1.0678 * roughness + 0.4573 * r2 - 0.8469 * rInv;
	float b = -0.6014 + 0.5538 * roughness - 0.4670 * r2 - 0.1255 * rInv;
	float DG = exp( a * dotNV + b );
	return saturate( DG );
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 fab = texture2D( dfgLUT, vec2( roughness, dotNV ) ).rg;
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 fab = texture2D( dfgLUT, vec2( roughness, dotNV ) ).rg;
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
vec3 BRDF_GGX_Multiscatter( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 singleScatter = BRDF_GGX( lightDir, viewDir, normal, material );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	vec2 dfgV = texture2D( dfgLUT, vec2( material.roughness, dotNV ) ).rg;
	vec2 dfgL = texture2D( dfgLUT, vec2( material.roughness, dotNL ) ).rg;
	vec3 FssEss_V = material.specularColorBlended * dfgV.x + material.specularF90 * dfgV.y;
	vec3 FssEss_L = material.specularColorBlended * dfgL.x + material.specularF90 * dfgL.y;
	float Ess_V = dfgV.x + dfgV.y;
	float Ess_L = dfgL.x + dfgL.y;
	float Ems_V = 1.0 - Ess_V;
	float Ems_L = 1.0 - Ess_L;
	vec3 Favg = material.specularColorBlended + ( 1.0 - material.specularColorBlended ) * 0.047619;
	vec3 Fms = FssEss_V * FssEss_L * Favg / ( 1.0 - Ems_V * Ems_L * Favg + EPSILON );
	float compensationFactor = Ems_V * Ems_L;
	vec3 multiScatter = Fms * compensationFactor;
	return singleScatter + multiScatter;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColorBlended * t2.x + ( vec3( 1.0 ) - material.specularColorBlended ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseContribution * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN
 
 		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );
 
 		float sheenAlbedoV = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
 		float sheenAlbedoL = IBLSheenBRDF( geometryNormal, directLight.direction, material.sheenRoughness );
 
 		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * max( sheenAlbedoV, sheenAlbedoL );
 
 		irradiance *= sheenEnergyComp;
 
 	#endif
	reflectedLight.directSpecular += irradiance * BRDF_GGX_Multiscatter( directLight.direction, geometryViewDir, geometryNormal, material );
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseContribution );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 diffuse = irradiance * BRDF_Lambert( material.diffuseContribution );
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		diffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectDiffuse += diffuse;
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness ) * RECIPROCAL_PI;
 	#endif
	vec3 singleScatteringDielectric = vec3( 0.0 );
	vec3 multiScatteringDielectric = vec3( 0.0 );
	vec3 singleScatteringMetallic = vec3( 0.0 );
	vec3 multiScatteringMetallic = vec3( 0.0 );
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.iridescence, material.iridescenceFresnelDielectric, material.roughness, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscatteringIridescence( geometryNormal, geometryViewDir, material.diffuseColor, material.specularF90, material.iridescence, material.iridescenceFresnelMetallic, material.roughness, singleScatteringMetallic, multiScatteringMetallic );
	#else
		computeMultiscattering( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.roughness, singleScatteringDielectric, multiScatteringDielectric );
		computeMultiscattering( geometryNormal, geometryViewDir, material.diffuseColor, material.specularF90, material.roughness, singleScatteringMetallic, multiScatteringMetallic );
	#endif
	vec3 singleScattering = mix( singleScatteringDielectric, singleScatteringMetallic, material.metalness );
	vec3 multiScattering = mix( multiScatteringDielectric, multiScatteringMetallic, material.metalness );
	vec3 totalScatteringDielectric = singleScatteringDielectric + multiScatteringDielectric;
	vec3 diffuse = material.diffuseContribution * ( 1.0 - totalScatteringDielectric );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	vec3 indirectSpecular = radiance * singleScattering;
	indirectSpecular += multiScattering * cosineWeightedIrradiance;
	vec3 indirectDiffuse = diffuse * cosineWeightedIrradiance;
	#ifdef USE_SHEEN
		float sheenAlbedo = IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
		float sheenEnergyComp = 1.0 - max3( material.sheenColor ) * sheenAlbedo;
		indirectSpecular *= sheenEnergyComp;
		indirectDiffuse *= sheenEnergyComp;
	#endif
	reflectedLight.indirectSpecular += indirectSpecular;
	reflectedLight.indirectDiffuse += indirectDiffuse;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,$h=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		material.iridescenceFresnelDielectric = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		material.iridescenceFresnelMetallic = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.diffuseColor );
		material.iridescenceFresnel = mix( material.iridescenceFresnelDielectric, material.iridescenceFresnelMetallic, material.metalness );
		material.iridescenceF0 = Schlick_to_F0( material.iridescenceFresnel, 1.0, dotNVi );
	}
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS ) && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,Kh=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD ) && defined( ENVMAP_TYPE_CUBE_UV )
		iblIrradiance += getIBLIrradiance( geometryNormal );
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		radiance += getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		radiance += getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,Qh=`#if defined( RE_IndirectDiffuse )
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,jh=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,eu=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,tu=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,nu=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,iu=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,su=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,ru=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,au=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,ou=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,lu=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,cu=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,hu=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,uu=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,du=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,fu=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,pu=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,mu=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,gu=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,_u=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,xu=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
	#endif
#endif`,vu=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,yu=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,Mu=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,Su=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,bu=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,Au=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,Tu=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	return depth * ( near - far ) - near;
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {
	return ( near * far ) / ( ( far - near ) * depth - far );
}`,Eu=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,wu=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,Cu=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,Ru=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,Iu=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,Pu=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,Lu=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#else
			uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		#endif
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform sampler2DShadow spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#else
			uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		#endif
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#if defined( SHADOWMAP_TYPE_PCF )
			uniform samplerCubeShadow pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#elif defined( SHADOWMAP_TYPE_BASIC )
			uniform samplerCube pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		#endif
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float interleavedGradientNoise( vec2 position ) {
			return fract( 52.9829189 * fract( dot( position, vec2( 0.06711056, 0.00583715 ) ) ) );
		}
		vec2 vogelDiskSample( int sampleIndex, int samplesCount, float phi ) {
			const float goldenAngle = 2.399963229728653;
			float r = sqrt( ( float( sampleIndex ) + 0.5 ) / float( samplesCount ) );
			float theta = float( sampleIndex ) * goldenAngle + phi;
			return vec2( cos( theta ), sin( theta ) ) * r;
		}
	#endif
	#if defined( SHADOWMAP_TYPE_PCF )
		float getShadow( sampler2DShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			shadowCoord.z += shadowBias;
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
				float radius = shadowRadius * texelSize.x;
				float phi = interleavedGradientNoise( gl_FragCoord.xy ) * 6.28318530718;
				shadow = (
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 0, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 1, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 2, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 3, 5, phi ) * radius, shadowCoord.z ) ) +
					texture( shadowMap, vec3( shadowCoord.xy + vogelDiskSample( 4, 5, phi ) * radius, shadowCoord.z ) )
				) * 0.2;
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#elif defined( SHADOWMAP_TYPE_VSM )
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			shadowCoord.z += shadowBias;
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				vec2 distribution = texture2D( shadowMap, shadowCoord.xy ).rg;
				float mean = distribution.x;
				float variance = distribution.y * distribution.y;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					float hard_shadow = step( mean, shadowCoord.z );
				#else
					float hard_shadow = step( shadowCoord.z, mean );
				#endif
				if ( hard_shadow == 1.0 ) {
					shadow = 1.0;
				} else {
					variance = max( variance, 0.0000001 );
					float d = shadowCoord.z - mean;
					float p_max = variance / ( variance + d * d );
					p_max = clamp( ( p_max - 0.3 ) / 0.65, 0.0, 1.0 );
					shadow = max( hard_shadow, p_max );
				}
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#else
		float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
			float shadow = 1.0;
			shadowCoord.xyz /= shadowCoord.w;
			shadowCoord.z += shadowBias;
			bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
			bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
			if ( frustumTest ) {
				float depth = texture2D( shadowMap, shadowCoord.xy ).r;
				#ifdef USE_REVERSED_DEPTH_BUFFER
					shadow = step( depth, shadowCoord.z );
				#else
					shadow = step( shadowCoord.z, depth );
				#endif
			}
			return mix( 1.0, shadow, shadowIntensity );
		}
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	#if defined( SHADOWMAP_TYPE_PCF )
	float getPointShadow( samplerCubeShadow shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 bd3D = normalize( lightToPosition );
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
			dp += shadowBias;
			float texelSize = shadowRadius / shadowMapSize.x;
			vec3 absDir = abs( bd3D );
			vec3 tangent = absDir.x > absDir.z ? vec3( 0.0, 1.0, 0.0 ) : vec3( 1.0, 0.0, 0.0 );
			tangent = normalize( cross( bd3D, tangent ) );
			vec3 bitangent = cross( bd3D, tangent );
			float phi = interleavedGradientNoise( gl_FragCoord.xy ) * 6.28318530718;
			shadow = (
				texture( shadowMap, vec4( bd3D + ( tangent * vogelDiskSample( 0, 5, phi ).x + bitangent * vogelDiskSample( 0, 5, phi ).y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * vogelDiskSample( 1, 5, phi ).x + bitangent * vogelDiskSample( 1, 5, phi ).y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * vogelDiskSample( 2, 5, phi ).x + bitangent * vogelDiskSample( 2, 5, phi ).y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * vogelDiskSample( 3, 5, phi ).x + bitangent * vogelDiskSample( 3, 5, phi ).y ) * texelSize, dp ) ) +
				texture( shadowMap, vec4( bd3D + ( tangent * vogelDiskSample( 4, 5, phi ).x + bitangent * vogelDiskSample( 4, 5, phi ).y ) * texelSize, dp ) )
			) * 0.2;
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#elif defined( SHADOWMAP_TYPE_BASIC )
	float getPointShadow( samplerCube shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		vec3 bd3D = normalize( lightToPosition );
		vec3 absVec = abs( lightToPosition );
		float viewSpaceZ = max( max( absVec.x, absVec.y ), absVec.z );
		if ( viewSpaceZ - shadowCameraFar <= 0.0 && viewSpaceZ - shadowCameraNear >= 0.0 ) {
			float dp = ( shadowCameraFar * ( viewSpaceZ - shadowCameraNear ) ) / ( viewSpaceZ * ( shadowCameraFar - shadowCameraNear ) );
			dp += shadowBias;
			float depth = textureCube( shadowMap, bd3D ).r;
			#ifdef USE_REVERSED_DEPTH_BUFFER
				shadow = step( depth, dp );
			#else
				shadow = step( dp, depth );
			#endif
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	#endif
	#endif
#endif`,Du=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,Uu=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	vec3 shadowWorldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,Nu=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0 && ( defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_BASIC ) )
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,Fu=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,Ou=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,Bu=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,zu=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,Vu=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,ku=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,Gu=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,Hu=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,Wu=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = inverseTransformDirection( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseContribution, material.specularColorBlended, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,Xu=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		#else
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,qu=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,Yu=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,Zu=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`,Ju=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`,$u=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,Ku=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Qu=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,ju=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float flipEnvMap;
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vec3( flipEnvMap * vWorldDirection.x, vWorldDirection.yz ) );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,ed=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,td=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,nd=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,id=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	#ifdef USE_REVERSED_DEPTH_BUFFER
		float fragCoordZ = vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ];
	#else
		float fragCoordZ = 0.5 * vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ] + 0.5;
	#endif
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,sd=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,rd=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main () {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = vec4( dist, 0.0, 0.0, 1.0 );
}`,ad=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,od=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,ld=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,cd=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,hd=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,ud=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,dd=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,fd=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,pd=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,md=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,gd=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,_d=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( normalize( normal ) * 0.5 + 0.5, diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,xd=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,vd=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,yd=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,Md=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
 
		outgoingLight = outgoingLight + sheenSpecularDirect + sheenSpecularIndirect;
 
 	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Sd=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,bd=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Ad=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,Td=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,Ed=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,wd=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,Cd=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,Rd=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,Le={alphahash_fragment:Kc,alphahash_pars_fragment:Qc,alphamap_fragment:jc,alphamap_pars_fragment:eh,alphatest_fragment:th,alphatest_pars_fragment:nh,aomap_fragment:ih,aomap_pars_fragment:sh,batching_pars_vertex:rh,batching_vertex:ah,begin_vertex:oh,beginnormal_vertex:lh,bsdfs:ch,iridescence_fragment:hh,bumpmap_pars_fragment:uh,clipping_planes_fragment:dh,clipping_planes_pars_fragment:fh,clipping_planes_pars_vertex:ph,clipping_planes_vertex:mh,color_fragment:gh,color_pars_fragment:_h,color_pars_vertex:xh,color_vertex:vh,common:yh,cube_uv_reflection_fragment:Mh,defaultnormal_vertex:Sh,displacementmap_pars_vertex:bh,displacementmap_vertex:Ah,emissivemap_fragment:Th,emissivemap_pars_fragment:Eh,colorspace_fragment:wh,colorspace_pars_fragment:Ch,envmap_fragment:Rh,envmap_common_pars_fragment:Ih,envmap_pars_fragment:Ph,envmap_pars_vertex:Lh,envmap_physical_pars_fragment:Hh,envmap_vertex:Dh,fog_vertex:Uh,fog_pars_vertex:Nh,fog_fragment:Fh,fog_pars_fragment:Oh,gradientmap_pars_fragment:Bh,lightmap_pars_fragment:zh,lights_lambert_fragment:Vh,lights_lambert_pars_fragment:kh,lights_pars_begin:Gh,lights_toon_fragment:Wh,lights_toon_pars_fragment:Xh,lights_phong_fragment:qh,lights_phong_pars_fragment:Yh,lights_physical_fragment:Zh,lights_physical_pars_fragment:Jh,lights_fragment_begin:$h,lights_fragment_maps:Kh,lights_fragment_end:Qh,logdepthbuf_fragment:jh,logdepthbuf_pars_fragment:eu,logdepthbuf_pars_vertex:tu,logdepthbuf_vertex:nu,map_fragment:iu,map_pars_fragment:su,map_particle_fragment:ru,map_particle_pars_fragment:au,metalnessmap_fragment:ou,metalnessmap_pars_fragment:lu,morphinstance_vertex:cu,morphcolor_vertex:hu,morphnormal_vertex:uu,morphtarget_pars_vertex:du,morphtarget_vertex:fu,normal_fragment_begin:pu,normal_fragment_maps:mu,normal_pars_fragment:gu,normal_pars_vertex:_u,normal_vertex:xu,normalmap_pars_fragment:vu,clearcoat_normal_fragment_begin:yu,clearcoat_normal_fragment_maps:Mu,clearcoat_pars_fragment:Su,iridescence_pars_fragment:bu,opaque_fragment:Au,packing:Tu,premultiplied_alpha_fragment:Eu,project_vertex:wu,dithering_fragment:Cu,dithering_pars_fragment:Ru,roughnessmap_fragment:Iu,roughnessmap_pars_fragment:Pu,shadowmap_pars_fragment:Lu,shadowmap_pars_vertex:Du,shadowmap_vertex:Uu,shadowmask_pars_fragment:Nu,skinbase_vertex:Fu,skinning_pars_vertex:Ou,skinning_vertex:Bu,skinnormal_vertex:zu,specularmap_fragment:Vu,specularmap_pars_fragment:ku,tonemapping_fragment:Gu,tonemapping_pars_fragment:Hu,transmission_fragment:Wu,transmission_pars_fragment:Xu,uv_pars_fragment:qu,uv_pars_vertex:Yu,uv_vertex:Zu,worldpos_vertex:Ju,background_vert:$u,background_frag:Ku,backgroundCube_vert:Qu,backgroundCube_frag:ju,cube_vert:ed,cube_frag:td,depth_vert:nd,depth_frag:id,distance_vert:sd,distance_frag:rd,equirect_vert:ad,equirect_frag:od,linedashed_vert:ld,linedashed_frag:cd,meshbasic_vert:hd,meshbasic_frag:ud,meshlambert_vert:dd,meshlambert_frag:fd,meshmatcap_vert:pd,meshmatcap_frag:md,meshnormal_vert:gd,meshnormal_frag:_d,meshphong_vert:xd,meshphong_frag:vd,meshphysical_vert:yd,meshphysical_frag:Md,meshtoon_vert:Sd,meshtoon_frag:bd,points_vert:Ad,points_frag:Td,shadow_vert:Ed,shadow_frag:wd,sprite_vert:Cd,sprite_frag:Rd},oe={common:{diffuse:{value:new He(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new Ie},alphaMap:{value:null},alphaMapTransform:{value:new Ie},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new Ie}},envmap:{envMap:{value:null},envMapRotation:{value:new Ie},flipEnvMap:{value:-1},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98},dfgLUT:{value:null}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new Ie}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new Ie}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new Ie},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new Ie},normalScale:{value:new Je(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new Ie},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new Ie}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new Ie}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new Ie}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new He(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMap:{value:[]},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotShadowMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMap:{value:[]},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null}},points:{diffuse:{value:new He(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new Ie},alphaTest:{value:0},uvTransform:{value:new Ie}},sprite:{diffuse:{value:new He(16777215)},opacity:{value:1},center:{value:new Je(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new Ie},alphaMap:{value:null},alphaMapTransform:{value:new Ie},alphaTest:{value:0}}},cn={basic:{uniforms:Mt([oe.common,oe.specularmap,oe.envmap,oe.aomap,oe.lightmap,oe.fog]),vertexShader:Le.meshbasic_vert,fragmentShader:Le.meshbasic_frag},lambert:{uniforms:Mt([oe.common,oe.specularmap,oe.envmap,oe.aomap,oe.lightmap,oe.emissivemap,oe.bumpmap,oe.normalmap,oe.displacementmap,oe.fog,oe.lights,{emissive:{value:new He(0)}}]),vertexShader:Le.meshlambert_vert,fragmentShader:Le.meshlambert_frag},phong:{uniforms:Mt([oe.common,oe.specularmap,oe.envmap,oe.aomap,oe.lightmap,oe.emissivemap,oe.bumpmap,oe.normalmap,oe.displacementmap,oe.fog,oe.lights,{emissive:{value:new He(0)},specular:{value:new He(1118481)},shininess:{value:30}}]),vertexShader:Le.meshphong_vert,fragmentShader:Le.meshphong_frag},standard:{uniforms:Mt([oe.common,oe.envmap,oe.aomap,oe.lightmap,oe.emissivemap,oe.bumpmap,oe.normalmap,oe.displacementmap,oe.roughnessmap,oe.metalnessmap,oe.fog,oe.lights,{emissive:{value:new He(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:Le.meshphysical_vert,fragmentShader:Le.meshphysical_frag},toon:{uniforms:Mt([oe.common,oe.aomap,oe.lightmap,oe.emissivemap,oe.bumpmap,oe.normalmap,oe.displacementmap,oe.gradientmap,oe.fog,oe.lights,{emissive:{value:new He(0)}}]),vertexShader:Le.meshtoon_vert,fragmentShader:Le.meshtoon_frag},matcap:{uniforms:Mt([oe.common,oe.bumpmap,oe.normalmap,oe.displacementmap,oe.fog,{matcap:{value:null}}]),vertexShader:Le.meshmatcap_vert,fragmentShader:Le.meshmatcap_frag},points:{uniforms:Mt([oe.points,oe.fog]),vertexShader:Le.points_vert,fragmentShader:Le.points_frag},dashed:{uniforms:Mt([oe.common,oe.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:Le.linedashed_vert,fragmentShader:Le.linedashed_frag},depth:{uniforms:Mt([oe.common,oe.displacementmap]),vertexShader:Le.depth_vert,fragmentShader:Le.depth_frag},normal:{uniforms:Mt([oe.common,oe.bumpmap,oe.normalmap,oe.displacementmap,{opacity:{value:1}}]),vertexShader:Le.meshnormal_vert,fragmentShader:Le.meshnormal_frag},sprite:{uniforms:Mt([oe.sprite,oe.fog]),vertexShader:Le.sprite_vert,fragmentShader:Le.sprite_frag},background:{uniforms:{uvTransform:{value:new Ie},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:Le.background_vert,fragmentShader:Le.background_frag},backgroundCube:{uniforms:{envMap:{value:null},flipEnvMap:{value:-1},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new Ie}},vertexShader:Le.backgroundCube_vert,fragmentShader:Le.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:Le.cube_vert,fragmentShader:Le.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:Le.equirect_vert,fragmentShader:Le.equirect_frag},distance:{uniforms:Mt([oe.common,oe.displacementmap,{referencePosition:{value:new F},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:Le.distance_vert,fragmentShader:Le.distance_frag},shadow:{uniforms:Mt([oe.lights,oe.fog,{color:{value:new He(0)},opacity:{value:1}}]),vertexShader:Le.shadow_vert,fragmentShader:Le.shadow_frag}};cn.physical={uniforms:Mt([cn.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new Ie},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new Ie},clearcoatNormalScale:{value:new Je(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new Ie},dispersion:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new Ie},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new Ie},sheen:{value:0},sheenColor:{value:new He(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new Ie},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new Ie},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new Ie},transmissionSamplerSize:{value:new Je},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new Ie},attenuationDistance:{value:0},attenuationColor:{value:new He(0)},specularColor:{value:new He(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new Ie},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new Ie},anisotropyVector:{value:new Je},anisotropyMap:{value:null},anisotropyMapTransform:{value:new Ie}}]),vertexShader:Le.meshphysical_vert,fragmentShader:Le.meshphysical_frag};var ea={r:0,b:0,g:0},ni=new nn,Id=new ut;function Pd(i,e,t,n,s,r,a){let o=new He(0),c=r===!0?0:1,l,h,f=null,p=0,d=null;function _(T){let A=T.isScene===!0?T.background:null;return A&&A.isTexture&&(A=(T.backgroundBlurriness>0?t:e).get(A)),A}function y(T){let A=!1,E=_(T);E===null?u(o,c):E&&E.isColor&&(u(E,1),A=!0);let w=i.xr.getEnvironmentBlendMode();w==="additive"?n.buffers.color.setClear(0,0,0,1,a):w==="alpha-blend"&&n.buffers.color.setClear(0,0,0,0,a),(i.autoClear||A)&&(n.buffers.depth.setTest(!0),n.buffers.depth.setMask(!0),n.buffers.color.setMask(!0),i.clear(i.autoClearColor,i.autoClearDepth,i.autoClearStencil))}function m(T,A){let E=_(A);E&&(E.isCubeTexture||E.mapping===ts)?(h===void 0&&(h=new Rt(new bi(1,1,1),new Ft({name:"BackgroundCubeMaterial",uniforms:ti(cn.backgroundCube.uniforms),vertexShader:cn.backgroundCube.vertexShader,fragmentShader:cn.backgroundCube.fragmentShader,side:Tt,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),h.geometry.deleteAttribute("normal"),h.geometry.deleteAttribute("uv"),h.onBeforeRender=function(w,I,B){this.matrixWorld.copyPosition(B.matrixWorld)},Object.defineProperty(h.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),s.update(h)),ni.copy(A.backgroundRotation),ni.x*=-1,ni.y*=-1,ni.z*=-1,E.isCubeTexture&&E.isRenderTargetTexture===!1&&(ni.y*=-1,ni.z*=-1),h.material.uniforms.envMap.value=E,h.material.uniforms.flipEnvMap.value=E.isCubeTexture&&E.isRenderTargetTexture===!1?-1:1,h.material.uniforms.backgroundBlurriness.value=A.backgroundBlurriness,h.material.uniforms.backgroundIntensity.value=A.backgroundIntensity,h.material.uniforms.backgroundRotation.value.setFromMatrix4(Id.makeRotationFromEuler(ni)),h.material.toneMapped=ze.getTransfer(E.colorSpace)!==Xe,(f!==E||p!==E.version||d!==i.toneMapping)&&(h.material.needsUpdate=!0,f=E,p=E.version,d=i.toneMapping),h.layers.enableAll(),T.unshift(h,h.geometry,h.material,0,0,null)):E&&E.isTexture&&(l===void 0&&(l=new Rt(new Kn(2,2),new Ft({name:"BackgroundMaterial",uniforms:ti(cn.background.uniforms),vertexShader:cn.background.vertexShader,fragmentShader:cn.background.fragmentShader,side:xn,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),l.geometry.deleteAttribute("normal"),Object.defineProperty(l.material,"map",{get:function(){return this.uniforms.t2D.value}}),s.update(l)),l.material.uniforms.t2D.value=E,l.material.uniforms.backgroundIntensity.value=A.backgroundIntensity,l.material.toneMapped=ze.getTransfer(E.colorSpace)!==Xe,E.matrixAutoUpdate===!0&&E.updateMatrix(),l.material.uniforms.uvTransform.value.copy(E.matrix),(f!==E||p!==E.version||d!==i.toneMapping)&&(l.material.needsUpdate=!0,f=E,p=E.version,d=i.toneMapping),l.layers.enableAll(),T.unshift(l,l.geometry,l.material,0,0,null))}function u(T,A){T.getRGB(ea,oo(i)),n.buffers.color.setClear(ea.r,ea.g,ea.b,A,a)}function b(){h!==void 0&&(h.geometry.dispose(),h.material.dispose(),h=void 0),l!==void 0&&(l.geometry.dispose(),l.material.dispose(),l=void 0)}return{getClearColor:function(){return o},setClearColor:function(T,A=1){o.set(T),c=A,u(o,c)},getClearAlpha:function(){return c},setClearAlpha:function(T){c=T,u(o,c)},render:y,addToRenderList:m,dispose:b}}function Ld(i,e){let t=i.getParameter(i.MAX_VERTEX_ATTRIBS),n={},s=p(null),r=s,a=!1;function o(M,L,V,z,W){let Y=!1,k=f(z,V,L);r!==k&&(r=k,l(r.object)),Y=d(M,z,V,W),Y&&_(M,z,V,W),W!==null&&e.update(W,i.ELEMENT_ARRAY_BUFFER),(Y||a)&&(a=!1,A(M,L,V,z),W!==null&&i.bindBuffer(i.ELEMENT_ARRAY_BUFFER,e.get(W).buffer))}function c(){return i.createVertexArray()}function l(M){return i.bindVertexArray(M)}function h(M){return i.deleteVertexArray(M)}function f(M,L,V){let z=V.wireframe===!0,W=n[M.id];W===void 0&&(W={},n[M.id]=W);let Y=W[L.id];Y===void 0&&(Y={},W[L.id]=Y);let k=Y[z];return k===void 0&&(k=p(c()),Y[z]=k),k}function p(M){let L=[],V=[],z=[];for(let W=0;W<t;W++)L[W]=0,V[W]=0,z[W]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:L,enabledAttributes:V,attributeDivisors:z,object:M,attributes:{},index:null}}function d(M,L,V,z){let W=r.attributes,Y=L.attributes,k=0,H=V.getAttributes();for(let $ in H)if(H[$].location>=0){let ae=W[$],ue=Y[$];if(ue===void 0&&($==="instanceMatrix"&&M.instanceMatrix&&(ue=M.instanceMatrix),$==="instanceColor"&&M.instanceColor&&(ue=M.instanceColor)),ae===void 0||ae.attribute!==ue||ue&&ae.data!==ue.data)return!0;k++}return r.attributesNum!==k||r.index!==z}function _(M,L,V,z){let W={},Y=L.attributes,k=0,H=V.getAttributes();for(let $ in H)if(H[$].location>=0){let ae=Y[$];ae===void 0&&($==="instanceMatrix"&&M.instanceMatrix&&(ae=M.instanceMatrix),$==="instanceColor"&&M.instanceColor&&(ae=M.instanceColor));let ue={};ue.attribute=ae,ae&&ae.data&&(ue.data=ae.data),W[$]=ue,k++}r.attributes=W,r.attributesNum=k,r.index=z}function y(){let M=r.newAttributes;for(let L=0,V=M.length;L<V;L++)M[L]=0}function m(M){u(M,0)}function u(M,L){let V=r.newAttributes,z=r.enabledAttributes,W=r.attributeDivisors;V[M]=1,z[M]===0&&(i.enableVertexAttribArray(M),z[M]=1),W[M]!==L&&(i.vertexAttribDivisor(M,L),W[M]=L)}function b(){let M=r.newAttributes,L=r.enabledAttributes;for(let V=0,z=L.length;V<z;V++)L[V]!==M[V]&&(i.disableVertexAttribArray(V),L[V]=0)}function T(M,L,V,z,W,Y,k){k===!0?i.vertexAttribIPointer(M,L,V,W,Y):i.vertexAttribPointer(M,L,V,z,W,Y)}function A(M,L,V,z){y();let W=z.attributes,Y=V.getAttributes(),k=L.defaultAttributeValues;for(let H in Y){let $=Y[H];if($.location>=0){let he=W[H];if(he===void 0&&(H==="instanceMatrix"&&M.instanceMatrix&&(he=M.instanceMatrix),H==="instanceColor"&&M.instanceColor&&(he=M.instanceColor)),he!==void 0){let ae=he.normalized,ue=he.itemSize,Fe=e.get(he);if(Fe===void 0)continue;let De=Fe.buffer,st=Fe.type,nt=Fe.bytesPerElement,q=st===i.INT||st===i.UNSIGNED_INT||he.gpuType===pr;if(he.isInterleavedBufferAttribute){let K=he.data,pe=K.stride,Pe=he.offset;if(K.isInstancedInterleavedBuffer){for(let _e=0;_e<$.locationSize;_e++)u($.location+_e,K.meshPerAttribute);M.isInstancedMesh!==!0&&z._maxInstanceCount===void 0&&(z._maxInstanceCount=K.meshPerAttribute*K.count)}else for(let _e=0;_e<$.locationSize;_e++)m($.location+_e);i.bindBuffer(i.ARRAY_BUFFER,De);for(let _e=0;_e<$.locationSize;_e++)T($.location+_e,ue/$.locationSize,st,ae,pe*nt,(Pe+ue/$.locationSize*_e)*nt,q)}else{if(he.isInstancedBufferAttribute){for(let K=0;K<$.locationSize;K++)u($.location+K,he.meshPerAttribute);M.isInstancedMesh!==!0&&z._maxInstanceCount===void 0&&(z._maxInstanceCount=he.meshPerAttribute*he.count)}else for(let K=0;K<$.locationSize;K++)m($.location+K);i.bindBuffer(i.ARRAY_BUFFER,De);for(let K=0;K<$.locationSize;K++)T($.location+K,ue/$.locationSize,st,ae,ue*nt,ue/$.locationSize*K*nt,q)}}else if(k!==void 0){let ae=k[H];if(ae!==void 0)switch(ae.length){case 2:i.vertexAttrib2fv($.location,ae);break;case 3:i.vertexAttrib3fv($.location,ae);break;case 4:i.vertexAttrib4fv($.location,ae);break;default:i.vertexAttrib1fv($.location,ae)}}}}b()}function E(){B();for(let M in n){let L=n[M];for(let V in L){let z=L[V];for(let W in z)h(z[W].object),delete z[W];delete L[V]}delete n[M]}}function w(M){if(n[M.id]===void 0)return;let L=n[M.id];for(let V in L){let z=L[V];for(let W in z)h(z[W].object),delete z[W];delete L[V]}delete n[M.id]}function I(M){for(let L in n){let V=n[L];if(V[M.id]===void 0)continue;let z=V[M.id];for(let W in z)h(z[W].object),delete z[W];delete V[M.id]}}function B(){v(),a=!0,r!==s&&(r=s,l(r.object))}function v(){s.geometry=null,s.program=null,s.wireframe=!1}return{setup:o,reset:B,resetDefaultState:v,dispose:E,releaseStatesOfGeometry:w,releaseStatesOfProgram:I,initAttributes:y,enableAttribute:m,disableUnusedAttributes:b}}function Dd(i,e,t){let n;function s(l){n=l}function r(l,h){i.drawArrays(n,l,h),t.update(h,n,1)}function a(l,h,f){f!==0&&(i.drawArraysInstanced(n,l,h,f),t.update(h,n,f))}function o(l,h,f){if(f===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(n,l,0,h,0,f);let d=0;for(let _=0;_<f;_++)d+=h[_];t.update(d,n,1)}function c(l,h,f,p){if(f===0)return;let d=e.get("WEBGL_multi_draw");if(d===null)for(let _=0;_<l.length;_++)a(l[_],h[_],p[_]);else{d.multiDrawArraysInstancedWEBGL(n,l,0,h,0,p,0,f);let _=0;for(let y=0;y<f;y++)_+=h[y]*p[y];t.update(_,n,1)}}this.setMode=s,this.render=r,this.renderInstances=a,this.renderMultiDraw=o,this.renderMultiDrawInstances=c}function Ud(i,e,t,n){let s;function r(){if(s!==void 0)return s;if(e.has("EXT_texture_filter_anisotropic")===!0){let I=e.get("EXT_texture_filter_anisotropic");s=i.getParameter(I.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else s=0;return s}function a(I){return!(I!==Ht&&n.convert(I)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_FORMAT))}function o(I){let B=I===on&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(I!==Bt&&n.convert(I)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_TYPE)&&I!==Kt&&!B)}function c(I){if(I==="highp"){if(i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.HIGH_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.HIGH_FLOAT).precision>0)return"highp";I="mediump"}return I==="mediump"&&i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.MEDIUM_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let l=t.precision!==void 0?t.precision:"highp",h=c(l);h!==l&&(Ce("WebGLRenderer:",l,"not supported, using",h,"instead."),l=h);let f=t.logarithmicDepthBuffer===!0,p=t.reversedDepthBuffer===!0&&e.has("EXT_clip_control"),d=i.getParameter(i.MAX_TEXTURE_IMAGE_UNITS),_=i.getParameter(i.MAX_VERTEX_TEXTURE_IMAGE_UNITS),y=i.getParameter(i.MAX_TEXTURE_SIZE),m=i.getParameter(i.MAX_CUBE_MAP_TEXTURE_SIZE),u=i.getParameter(i.MAX_VERTEX_ATTRIBS),b=i.getParameter(i.MAX_VERTEX_UNIFORM_VECTORS),T=i.getParameter(i.MAX_VARYING_VECTORS),A=i.getParameter(i.MAX_FRAGMENT_UNIFORM_VECTORS),E=i.getParameter(i.MAX_SAMPLES),w=i.getParameter(i.SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:r,getMaxPrecision:c,textureFormatReadable:a,textureTypeReadable:o,precision:l,logarithmicDepthBuffer:f,reversedDepthBuffer:p,maxTextures:d,maxVertexTextures:_,maxTextureSize:y,maxCubemapSize:m,maxAttributes:u,maxVertexUniforms:b,maxVaryings:T,maxFragmentUniforms:A,maxSamples:E,samples:w}}function Nd(i){let e=this,t=null,n=0,s=!1,r=!1,a=new jt,o=new Ie,c={value:null,needsUpdate:!1};this.uniform=c,this.numPlanes=0,this.numIntersection=0,this.init=function(f,p){let d=f.length!==0||p||n!==0||s;return s=p,n=f.length,d},this.beginShadows=function(){r=!0,h(null)},this.endShadows=function(){r=!1},this.setGlobalState=function(f,p){t=h(f,p,0)},this.setState=function(f,p,d){let _=f.clippingPlanes,y=f.clipIntersection,m=f.clipShadows,u=i.get(f);if(!s||_===null||_.length===0||r&&!m)r?h(null):l();else{let b=r?0:n,T=b*4,A=u.clippingState||null;c.value=A,A=h(_,p,T,d);for(let E=0;E!==T;++E)A[E]=t[E];u.clippingState=A,this.numIntersection=y?this.numPlanes:0,this.numPlanes+=b}};function l(){c.value!==t&&(c.value=t,c.needsUpdate=n>0),e.numPlanes=n,e.numIntersection=0}function h(f,p,d,_){let y=f!==null?f.length:0,m=null;if(y!==0){if(m=c.value,_!==!0||m===null){let u=d+y*4,b=p.matrixWorldInverse;o.getNormalMatrix(b),(m===null||m.length<u)&&(m=new Float32Array(u));for(let T=0,A=d;T!==y;++T,A+=4)a.copy(f[T]).applyMatrix4(b,o),a.normal.toArray(m,A),m[A+3]=a.constant}c.value=m,c.needsUpdate=!0}return e.numPlanes=y,e.numIntersection=0,m}}function Fd(i){let e=new WeakMap;function t(a,o){return o===ur?a.mapping=Nn:o===dr&&(a.mapping=jn),a}function n(a){if(a&&a.isTexture){let o=a.mapping;if(o===ur||o===dr)if(e.has(a)){let c=e.get(a).texture;return t(c,a.mapping)}else{let c=a.image;if(c&&c.height>0){let l=new Yi(c.height);return l.fromEquirectangularTexture(i,a),e.set(a,l),a.addEventListener("dispose",s),t(l.texture,a.mapping)}else return null}}return a}function s(a){let o=a.target;o.removeEventListener("dispose",s);let c=e.get(o);c!==void 0&&(e.delete(o),c.dispose())}function r(){e=new WeakMap}return{get:n,dispose:r}}var Bn=4,Fl=[.125,.215,.35,.446,.526,.582],si=20,Od=256,ls=new ji,Ol=new He,uo=null,fo=0,po=0,mo=!1,Bd=new F,na=class{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._sizeLods=[],this._sigmas=[],this._lodMeshes=[],this._backgroundBox=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._blurMaterial=null,this._ggxMaterial=null}fromScene(e,t=0,n=.1,s=100,r={}){let{size:a=256,position:o=Bd}=r;uo=this._renderer.getRenderTarget(),fo=this._renderer.getActiveCubeFace(),po=this._renderer.getActiveMipmapLevel(),mo=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(a);let c=this._allocateTargets();return c.depthBuffer=!0,this._sceneToCubeUV(e,n,s,c,o),t>0&&this._blur(c,0,0,t),this._applyPMREM(c),this._cleanup(c),c}fromEquirectangular(e,t=null){return this._fromTexture(e,t)}fromCubemap(e,t=null){return this._fromTexture(e,t)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=Vl(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=zl(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose(),this._backgroundBox!==null&&(this._backgroundBox.geometry.dispose(),this._backgroundBox.material.dispose())}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._ggxMaterial!==null&&this._ggxMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodMeshes.length;e++)this._lodMeshes[e].geometry.dispose()}_cleanup(e){this._renderer.setRenderTarget(uo,fo,po),this._renderer.xr.enabled=mo,e.scissorTest=!1,Ci(e,0,0,e.width,e.height)}_fromTexture(e,t){e.mapping===Nn||e.mapping===jn?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),uo=this._renderer.getRenderTarget(),fo=this._renderer.getActiveCubeFace(),po=this._renderer.getActiveMipmapLevel(),mo=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;let n=t||this._allocateTargets();return this._textureToCubeUV(e,n),this._applyPMREM(n),this._cleanup(n),n}_allocateTargets(){let e=3*Math.max(this._cubeSize,112),t=4*this._cubeSize,n={magFilter:_t,minFilter:_t,generateMipmaps:!1,type:on,format:Ht,colorSpace:Zn,depthBuffer:!1},s=Bl(e,t,n);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==t){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=Bl(e,t,n);let{_lodMax:r}=this;({lodMeshes:this._lodMeshes,sizeLods:this._sizeLods,sigmas:this._sigmas}=zd(r)),this._blurMaterial=kd(r,e,t),this._ggxMaterial=Vd(r,e,t)}return s}_compileMaterial(e){let t=new Rt(new sn,e);this._renderer.compile(t,ls)}_sceneToCubeUV(e,t,n,s,r){let c=new yt(90,1,t,n),l=[1,-1,1,1,1,1],h=[1,1,1,-1,-1,-1],f=this._renderer,p=f.autoClear,d=f.toneMapping;f.getClearColor(Ol),f.toneMapping=Jt,f.autoClear=!1,f.state.buffers.depth.getReversed()&&(f.setRenderTarget(s),f.clearDepth(),f.setRenderTarget(null)),this._backgroundBox===null&&(this._backgroundBox=new Rt(new bi,new $n({name:"PMREM.Background",side:Tt,depthWrite:!1,depthTest:!1})));let y=this._backgroundBox,m=y.material,u=!1,b=e.background;b?b.isColor&&(m.color.copy(b),e.background=null,u=!0):(m.color.copy(Ol),u=!0);for(let T=0;T<6;T++){let A=T%3;A===0?(c.up.set(0,l[T],0),c.position.set(r.x,r.y,r.z),c.lookAt(r.x+h[T],r.y,r.z)):A===1?(c.up.set(0,0,l[T]),c.position.set(r.x,r.y,r.z),c.lookAt(r.x,r.y+h[T],r.z)):(c.up.set(0,l[T],0),c.position.set(r.x,r.y,r.z),c.lookAt(r.x,r.y,r.z+h[T]));let E=this._cubeSize;Ci(s,A*E,T>2?E:0,E,E),f.setRenderTarget(s),u&&f.render(y,c),f.render(e,c)}f.toneMapping=d,f.autoClear=p,e.background=b}_textureToCubeUV(e,t){let n=this._renderer,s=e.mapping===Nn||e.mapping===jn;s?(this._cubemapMaterial===null&&(this._cubemapMaterial=Vl()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=zl());let r=s?this._cubemapMaterial:this._equirectMaterial,a=this._lodMeshes[0];a.material=r;let o=r.uniforms;o.envMap.value=e;let c=this._cubeSize;Ci(t,0,0,3*c,2*c),n.setRenderTarget(t),n.render(a,ls)}_applyPMREM(e){let t=this._renderer,n=t.autoClear;t.autoClear=!1;let s=this._lodMeshes.length;for(let r=1;r<s;r++)this._applyGGXFilter(e,r-1,r);t.autoClear=n}_applyGGXFilter(e,t,n){let s=this._renderer,r=this._pingPongRenderTarget,a=this._ggxMaterial,o=this._lodMeshes[n];o.material=a;let c=a.uniforms,l=n/(this._lodMeshes.length-1),h=t/(this._lodMeshes.length-1),f=Math.sqrt(l*l-h*h),p=0+l*1.25,d=f*p,{_lodMax:_}=this,y=this._sizeLods[n],m=3*y*(n>_-Bn?n-_+Bn:0),u=4*(this._cubeSize-y);c.envMap.value=e.texture,c.roughness.value=d,c.mipInt.value=_-t,Ci(r,m,u,3*y,2*y),s.setRenderTarget(r),s.render(o,ls),c.envMap.value=r.texture,c.roughness.value=0,c.mipInt.value=_-n,Ci(e,m,u,3*y,2*y),s.setRenderTarget(e),s.render(o,ls)}_blur(e,t,n,s,r){let a=this._pingPongRenderTarget;this._halfBlur(e,a,t,n,s,"latitudinal",r),this._halfBlur(a,e,n,n,s,"longitudinal",r)}_halfBlur(e,t,n,s,r,a,o){let c=this._renderer,l=this._blurMaterial;a!=="latitudinal"&&a!=="longitudinal"&&Ee("blur direction must be either latitudinal or longitudinal!");let h=3,f=this._lodMeshes[s];f.material=l;let p=l.uniforms,d=this._sizeLods[n]-1,_=isFinite(r)?Math.PI/(2*d):2*Math.PI/(2*si-1),y=r/_,m=isFinite(r)?1+Math.floor(h*y):si;m>si&&Ce(`sigmaRadians, ${r}, is too large and will clip, as it requested ${m} samples when the maximum is set to ${si}`);let u=[],b=0;for(let I=0;I<si;++I){let B=I/y,v=Math.exp(-B*B/2);u.push(v),I===0?b+=v:I<m&&(b+=2*v)}for(let I=0;I<u.length;I++)u[I]=u[I]/b;p.envMap.value=e.texture,p.samples.value=m,p.weights.value=u,p.latitudinal.value=a==="latitudinal",o&&(p.poleAxis.value=o);let{_lodMax:T}=this;p.dTheta.value=_,p.mipInt.value=T-n;let A=this._sizeLods[s],E=3*A*(s>T-Bn?s-T+Bn:0),w=4*(this._cubeSize-A);Ci(t,E,w,3*A,2*A),c.setRenderTarget(t),c.render(f,ls)}};function zd(i){let e=[],t=[],n=[],s=i,r=i-Bn+1+Fl.length;for(let a=0;a<r;a++){let o=Math.pow(2,s);e.push(o);let c=1/o;a>i-Bn?c=Fl[a-i+Bn-1]:a===0&&(c=0),t.push(c);let l=1/(o-2),h=-l,f=1+l,p=[h,h,f,h,f,f,h,h,f,f,h,f],d=6,_=6,y=3,m=2,u=1,b=new Float32Array(y*_*d),T=new Float32Array(m*_*d),A=new Float32Array(u*_*d);for(let w=0;w<d;w++){let I=w%3*2/3-1,B=w>2?0:-1,v=[I,B,0,I+2/3,B,0,I+2/3,B+1,0,I,B,0,I+2/3,B+1,0,I,B+1,0];b.set(v,y*_*w),T.set(p,m*_*w);let M=[w,w,w,w,w,w];A.set(M,u*_*w)}let E=new sn;E.setAttribute("position",new Ut(b,y)),E.setAttribute("uv",new Ut(T,m)),E.setAttribute("faceIndex",new Ut(A,u)),n.push(new Rt(E,null)),s>Bn&&s--}return{lodMeshes:n,sizeLods:e,sigmas:t}}function Bl(i,e,t){let n=new Nt(i,e,t);return n.texture.mapping=ts,n.texture.name="PMREM.cubeUv",n.scissorTest=!0,n}function Ci(i,e,t,n,s){i.viewport.set(e,t,n,s),i.scissor.set(e,t,n,s)}function Vd(i,e,t){return new Ft({name:"PMREMGGXConvolution",defines:{GGX_SAMPLES:Od,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},roughness:{value:0},mipInt:{value:0}},vertexShader:sa(),fragmentShader:`

			precision highp float;
			precision highp int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform float roughness;
			uniform float mipInt;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			#define PI 3.14159265359

			// Van der Corput radical inverse
			float radicalInverse_VdC(uint bits) {
				bits = (bits << 16u) | (bits >> 16u);
				bits = ((bits & 0x55555555u) << 1u) | ((bits & 0xAAAAAAAAu) >> 1u);
				bits = ((bits & 0x33333333u) << 2u) | ((bits & 0xCCCCCCCCu) >> 2u);
				bits = ((bits & 0x0F0F0F0Fu) << 4u) | ((bits & 0xF0F0F0F0u) >> 4u);
				bits = ((bits & 0x00FF00FFu) << 8u) | ((bits & 0xFF00FF00u) >> 8u);
				return float(bits) * 2.3283064365386963e-10; // / 0x100000000
			}

			// Hammersley sequence
			vec2 hammersley(uint i, uint N) {
				return vec2(float(i) / float(N), radicalInverse_VdC(i));
			}

			// GGX VNDF importance sampling (Eric Heitz 2018)
			// "Sampling the GGX Distribution of Visible Normals"
			// https://jcgt.org/published/0007/04/01/
			vec3 importanceSampleGGX_VNDF(vec2 Xi, vec3 V, float roughness) {
				float alpha = roughness * roughness;

				// Section 3.2: Transform view direction to hemisphere configuration
				vec3 Vh = normalize(vec3(alpha * V.x, alpha * V.y, V.z));

				// Section 4.1: Orthonormal basis
				float lensq = Vh.x * Vh.x + Vh.y * Vh.y;
				vec3 T1 = lensq > 0.0 ? vec3(-Vh.y, Vh.x, 0.0) / sqrt(lensq) : vec3(1.0, 0.0, 0.0);
				vec3 T2 = cross(Vh, T1);

				// Section 4.2: Parameterization of projected area
				float r = sqrt(Xi.x);
				float phi = 2.0 * PI * Xi.y;
				float t1 = r * cos(phi);
				float t2 = r * sin(phi);
				float s = 0.5 * (1.0 + Vh.z);
				t2 = (1.0 - s) * sqrt(1.0 - t1 * t1) + s * t2;

				// Section 4.3: Reprojection onto hemisphere
				vec3 Nh = t1 * T1 + t2 * T2 + sqrt(max(0.0, 1.0 - t1 * t1 - t2 * t2)) * Vh;

				// Section 3.4: Transform back to ellipsoid configuration
				return normalize(vec3(alpha * Nh.x, alpha * Nh.y, max(0.0, Nh.z)));
			}

			void main() {
				vec3 N = normalize(vOutputDirection);
				vec3 V = N; // Assume view direction equals normal for pre-filtering

				vec3 prefilteredColor = vec3(0.0);
				float totalWeight = 0.0;

				// For very low roughness, just sample the environment directly
				if (roughness < 0.001) {
					gl_FragColor = vec4(bilinearCubeUV(envMap, N, mipInt), 1.0);
					return;
				}

				// Tangent space basis for VNDF sampling
				vec3 up = abs(N.z) < 0.999 ? vec3(0.0, 0.0, 1.0) : vec3(1.0, 0.0, 0.0);
				vec3 tangent = normalize(cross(up, N));
				vec3 bitangent = cross(N, tangent);

				for(uint i = 0u; i < uint(GGX_SAMPLES); i++) {
					vec2 Xi = hammersley(i, uint(GGX_SAMPLES));

					// For PMREM, V = N, so in tangent space V is always (0, 0, 1)
					vec3 H_tangent = importanceSampleGGX_VNDF(Xi, vec3(0.0, 0.0, 1.0), roughness);

					// Transform H back to world space
					vec3 H = normalize(tangent * H_tangent.x + bitangent * H_tangent.y + N * H_tangent.z);
					vec3 L = normalize(2.0 * dot(V, H) * H - V);

					float NdotL = max(dot(N, L), 0.0);

					if(NdotL > 0.0) {
						// Sample environment at fixed mip level
						// VNDF importance sampling handles the distribution filtering
						vec3 sampleColor = bilinearCubeUV(envMap, L, mipInt);

						// Weight by NdotL for the split-sum approximation
						// VNDF PDF naturally accounts for the visible microfacet distribution
						prefilteredColor += sampleColor * NdotL;
						totalWeight += NdotL;
					}
				}

				if (totalWeight > 0.0) {
					prefilteredColor = prefilteredColor / totalWeight;
				}

				gl_FragColor = vec4(prefilteredColor, 1.0);
			}
		`,blending:an,depthTest:!1,depthWrite:!1})}function kd(i,e,t){let n=new Float32Array(si),s=new F(0,1,0);return new Ft({name:"SphericalGaussianBlur",defines:{n:si,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},samples:{value:1},weights:{value:n},latitudinal:{value:!1},dTheta:{value:0},mipInt:{value:0},poleAxis:{value:s}},vertexShader:sa(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform int samples;
			uniform float weights[ n ];
			uniform bool latitudinal;
			uniform float dTheta;
			uniform float mipInt;
			uniform vec3 poleAxis;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			vec3 getSample( float theta, vec3 axis ) {

				float cosTheta = cos( theta );
				// Rodrigues' axis-angle rotation
				vec3 sampleDirection = vOutputDirection * cosTheta
					+ cross( axis, vOutputDirection ) * sin( theta )
					+ axis * dot( axis, vOutputDirection ) * ( 1.0 - cosTheta );

				return bilinearCubeUV( envMap, sampleDirection, mipInt );

			}

			void main() {

				vec3 axis = latitudinal ? poleAxis : cross( poleAxis, vOutputDirection );

				if ( all( equal( axis, vec3( 0.0 ) ) ) ) {

					axis = vec3( vOutputDirection.z, 0.0, - vOutputDirection.x );

				}

				axis = normalize( axis );

				gl_FragColor = vec4( 0.0, 0.0, 0.0, 1.0 );
				gl_FragColor.rgb += weights[ 0 ] * getSample( 0.0, axis );

				for ( int i = 1; i < n; i++ ) {

					if ( i >= samples ) {

						break;

					}

					float theta = dTheta * float( i );
					gl_FragColor.rgb += weights[ i ] * getSample( -1.0 * theta, axis );
					gl_FragColor.rgb += weights[ i ] * getSample( theta, axis );

				}

			}
		`,blending:an,depthTest:!1,depthWrite:!1})}function zl(){return new Ft({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:sa(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,blending:an,depthTest:!1,depthWrite:!1})}function Vl(){return new Ft({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:sa(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:an,depthTest:!1,depthWrite:!1})}function sa(){return`

		precision mediump float;
		precision mediump int;

		attribute float faceIndex;

		varying vec3 vOutputDirection;

		// RH coordinate system; PMREM face-indexing convention
		vec3 getDirection( vec2 uv, float face ) {

			uv = 2.0 * uv - 1.0;

			vec3 direction = vec3( uv, 1.0 );

			if ( face == 0.0 ) {

				direction = direction.zyx; // ( 1, v, u ) pos x

			} else if ( face == 1.0 ) {

				direction = direction.xzy;
				direction.xz *= -1.0; // ( -u, 1, -v ) pos y

			} else if ( face == 2.0 ) {

				direction.x *= -1.0; // ( -u, v, 1 ) pos z

			} else if ( face == 3.0 ) {

				direction = direction.zyx;
				direction.xz *= -1.0; // ( -1, v, -u ) neg x

			} else if ( face == 4.0 ) {

				direction = direction.xzy;
				direction.xy *= -1.0; // ( -u, -1, v ) neg y

			} else if ( face == 5.0 ) {

				direction.z *= -1.0; // ( u, v, -1 ) neg z

			}

			return direction;

		}

		void main() {

			vOutputDirection = getDirection( uv, faceIndex );
			gl_Position = vec4( position, 1.0 );

		}
	`}function Gd(i){let e=new WeakMap,t=null;function n(o){if(o&&o.isTexture){let c=o.mapping,l=c===ur||c===dr,h=c===Nn||c===jn;if(l||h){let f=e.get(o),p=f!==void 0?f.texture.pmremVersion:0;if(o.isRenderTargetTexture&&o.pmremVersion!==p)return t===null&&(t=new na(i)),f=l?t.fromEquirectangular(o,f):t.fromCubemap(o,f),f.texture.pmremVersion=o.pmremVersion,e.set(o,f),f.texture;if(f!==void 0)return f.texture;{let d=o.image;return l&&d&&d.height>0||h&&d&&s(d)?(t===null&&(t=new na(i)),f=l?t.fromEquirectangular(o):t.fromCubemap(o),f.texture.pmremVersion=o.pmremVersion,e.set(o,f),o.addEventListener("dispose",r),f.texture):null}}}return o}function s(o){let c=0,l=6;for(let h=0;h<l;h++)o[h]!==void 0&&c++;return c===l}function r(o){let c=o.target;c.removeEventListener("dispose",r);let l=e.get(c);l!==void 0&&(e.delete(c),l.dispose())}function a(){e=new WeakMap,t!==null&&(t.dispose(),t=null)}return{get:n,dispose:a}}function Hd(i){let e={};function t(n){if(e[n]!==void 0)return e[n];let s=i.getExtension(n);return e[n]=s,s}return{has:function(n){return t(n)!==null},init:function(){t("EXT_color_buffer_float"),t("WEBGL_clip_cull_distance"),t("OES_texture_float_linear"),t("EXT_color_buffer_half_float"),t("WEBGL_multisampled_render_to_texture"),t("WEBGL_render_shared_exponent")},get:function(n){let s=t(n);return s===null&&yi("WebGLRenderer: "+n+" extension not supported."),s}}}function Wd(i,e,t,n){let s={},r=new WeakMap;function a(f){let p=f.target;p.index!==null&&e.remove(p.index);for(let _ in p.attributes)e.remove(p.attributes[_]);p.removeEventListener("dispose",a),delete s[p.id];let d=r.get(p);d&&(e.remove(d),r.delete(p)),n.releaseStatesOfGeometry(p),p.isInstancedBufferGeometry===!0&&delete p._maxInstanceCount,t.memory.geometries--}function o(f,p){return s[p.id]===!0||(p.addEventListener("dispose",a),s[p.id]=!0,t.memory.geometries++),p}function c(f){let p=f.attributes;for(let d in p)e.update(p[d],i.ARRAY_BUFFER)}function l(f){let p=[],d=f.index,_=f.attributes.position,y=0;if(d!==null){let b=d.array;y=d.version;for(let T=0,A=b.length;T<A;T+=3){let E=b[T+0],w=b[T+1],I=b[T+2];p.push(E,w,w,I,I,E)}}else if(_!==void 0){let b=_.array;y=_.version;for(let T=0,A=b.length/3-1;T<A;T+=3){let E=T+0,w=T+1,I=T+2;p.push(E,w,w,I,I,E)}}else return;let m=new(ro(p)?Wi:Hi)(p,1);m.version=y;let u=r.get(f);u&&e.remove(u),r.set(f,m)}function h(f){let p=r.get(f);if(p){let d=f.index;d!==null&&p.version<d.version&&l(f)}else l(f);return r.get(f)}return{get:o,update:c,getWireframeAttribute:h}}function Xd(i,e,t){let n;function s(p){n=p}let r,a;function o(p){r=p.type,a=p.bytesPerElement}function c(p,d){i.drawElements(n,d,r,p*a),t.update(d,n,1)}function l(p,d,_){_!==0&&(i.drawElementsInstanced(n,d,r,p*a,_),t.update(d,n,_))}function h(p,d,_){if(_===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(n,d,0,r,p,0,_);let m=0;for(let u=0;u<_;u++)m+=d[u];t.update(m,n,1)}function f(p,d,_,y){if(_===0)return;let m=e.get("WEBGL_multi_draw");if(m===null)for(let u=0;u<p.length;u++)l(p[u]/a,d[u],y[u]);else{m.multiDrawElementsInstancedWEBGL(n,d,0,r,p,0,y,0,_);let u=0;for(let b=0;b<_;b++)u+=d[b]*y[b];t.update(u,n,1)}}this.setMode=s,this.setIndex=o,this.render=c,this.renderInstances=l,this.renderMultiDraw=h,this.renderMultiDrawInstances=f}function qd(i){let e={geometries:0,textures:0},t={frame:0,calls:0,triangles:0,points:0,lines:0};function n(r,a,o){switch(t.calls++,a){case i.TRIANGLES:t.triangles+=o*(r/3);break;case i.LINES:t.lines+=o*(r/2);break;case i.LINE_STRIP:t.lines+=o*(r-1);break;case i.LINE_LOOP:t.lines+=o*r;break;case i.POINTS:t.points+=o*r;break;default:Ee("WebGLInfo: Unknown draw mode:",a);break}}function s(){t.calls=0,t.triangles=0,t.points=0,t.lines=0}return{memory:e,render:t,programs:null,autoReset:!0,reset:s,update:n}}function Yd(i,e,t){let n=new WeakMap,s=new ot;function r(a,o,c){let l=a.morphTargetInfluences,h=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,f=h!==void 0?h.length:0,p=n.get(o);if(p===void 0||p.count!==f){let v=function(){I.dispose(),n.delete(o),o.removeEventListener("dispose",v)};p!==void 0&&p.texture.dispose();let d=o.morphAttributes.position!==void 0,_=o.morphAttributes.normal!==void 0,y=o.morphAttributes.color!==void 0,m=o.morphAttributes.position||[],u=o.morphAttributes.normal||[],b=o.morphAttributes.color||[],T=0;d===!0&&(T=1),_===!0&&(T=2),y===!0&&(T=3);let A=o.attributes.position.count*T,E=1;A>e.maxTextureSize&&(E=Math.ceil(A/e.maxTextureSize),A=e.maxTextureSize);let w=new Float32Array(A*E*4*f),I=new ki(w,A,E,f);I.type=Kt,I.needsUpdate=!0;let B=T*4;for(let M=0;M<f;M++){let L=m[M],V=u[M],z=b[M],W=A*E*4*M;for(let Y=0;Y<L.count;Y++){let k=Y*B;d===!0&&(s.fromBufferAttribute(L,Y),w[W+k+0]=s.x,w[W+k+1]=s.y,w[W+k+2]=s.z,w[W+k+3]=0),_===!0&&(s.fromBufferAttribute(V,Y),w[W+k+4]=s.x,w[W+k+5]=s.y,w[W+k+6]=s.z,w[W+k+7]=0),y===!0&&(s.fromBufferAttribute(z,Y),w[W+k+8]=s.x,w[W+k+9]=s.y,w[W+k+10]=s.z,w[W+k+11]=z.itemSize===4?s.w:1)}}p={count:f,texture:I,size:new Je(A,E)},n.set(o,p),o.addEventListener("dispose",v)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)c.getUniforms().setValue(i,"morphTexture",a.morphTexture,t);else{let d=0;for(let y=0;y<l.length;y++)d+=l[y];let _=o.morphTargetsRelative?1:1-d;c.getUniforms().setValue(i,"morphTargetBaseInfluence",_),c.getUniforms().setValue(i,"morphTargetInfluences",l)}c.getUniforms().setValue(i,"morphTargetsTexture",p.texture,t),c.getUniforms().setValue(i,"morphTargetsTextureSize",p.size)}return{update:r}}function Zd(i,e,t,n){let s=new WeakMap;function r(c){let l=n.render.frame,h=c.geometry,f=e.get(c,h);if(s.get(f)!==l&&(e.update(f),s.set(f,l)),c.isInstancedMesh&&(c.hasEventListener("dispose",o)===!1&&c.addEventListener("dispose",o),s.get(c)!==l&&(t.update(c.instanceMatrix,i.ARRAY_BUFFER),c.instanceColor!==null&&t.update(c.instanceColor,i.ARRAY_BUFFER),s.set(c,l))),c.isSkinnedMesh){let p=c.skeleton;s.get(p)!==l&&(p.update(),s.set(p,l))}return f}function a(){s=new WeakMap}function o(c){let l=c.target;l.removeEventListener("dispose",o),t.remove(l.instanceMatrix),l.instanceColor!==null&&t.remove(l.instanceColor)}return{update:r,dispose:a}}var Jd={[Ha]:"LINEAR_TONE_MAPPING",[Wa]:"REINHARD_TONE_MAPPING",[Xa]:"CINEON_TONE_MAPPING",[qa]:"ACES_FILMIC_TONE_MAPPING",[Za]:"AGX_TONE_MAPPING",[Ja]:"NEUTRAL_TONE_MAPPING",[Ya]:"CUSTOM_TONE_MAPPING"};function $d(i,e,t,n,s){let r=new Nt(e,t,{type:i,depthBuffer:n,stencilBuffer:s}),a=new Nt(e,t,{type:on,depthBuffer:!1,stencilBuffer:!1}),o=new sn;o.setAttribute("position",new kt([-1,3,0,-1,-1,0,3,-1,0],3)),o.setAttribute("uv",new kt([0,2,0,0,2,0],2));let c=new Xs({uniforms:{tDiffuse:{value:null}},vertexShader:`
			precision highp float;

			uniform mat4 modelViewMatrix;
			uniform mat4 projectionMatrix;

			attribute vec3 position;
			attribute vec2 uv;

			varying vec2 vUv;

			void main() {
				vUv = uv;
				gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
			}`,fragmentShader:`
			precision highp float;

			uniform sampler2D tDiffuse;

			varying vec2 vUv;

			#include <tonemapping_pars_fragment>
			#include <colorspace_pars_fragment>

			void main() {
				gl_FragColor = texture2D( tDiffuse, vUv );

				#ifdef LINEAR_TONE_MAPPING
					gl_FragColor.rgb = LinearToneMapping( gl_FragColor.rgb );
				#elif defined( REINHARD_TONE_MAPPING )
					gl_FragColor.rgb = ReinhardToneMapping( gl_FragColor.rgb );
				#elif defined( CINEON_TONE_MAPPING )
					gl_FragColor.rgb = CineonToneMapping( gl_FragColor.rgb );
				#elif defined( ACES_FILMIC_TONE_MAPPING )
					gl_FragColor.rgb = ACESFilmicToneMapping( gl_FragColor.rgb );
				#elif defined( AGX_TONE_MAPPING )
					gl_FragColor.rgb = AgXToneMapping( gl_FragColor.rgb );
				#elif defined( NEUTRAL_TONE_MAPPING )
					gl_FragColor.rgb = NeutralToneMapping( gl_FragColor.rgb );
				#elif defined( CUSTOM_TONE_MAPPING )
					gl_FragColor.rgb = CustomToneMapping( gl_FragColor.rgb );
				#endif

				#ifdef SRGB_TRANSFER
					gl_FragColor = sRGBTransferOETF( gl_FragColor );
				#endif
			}`,depthTest:!1,depthWrite:!1}),l=new Rt(o,c),h=new ji(-1,1,1,-1,0,1),f=null,p=null,d=!1,_,y=null,m=[],u=!1;this.setSize=function(b,T){r.setSize(b,T),a.setSize(b,T);for(let A=0;A<m.length;A++){let E=m[A];E.setSize&&E.setSize(b,T)}},this.setEffects=function(b){m=b,u=m.length>0&&m[0].isRenderPass===!0;let T=r.width,A=r.height;for(let E=0;E<m.length;E++){let w=m[E];w.setSize&&w.setSize(T,A)}},this.begin=function(b,T){if(d||b.toneMapping===Jt&&m.length===0)return!1;if(y=T,T!==null){let A=T.width,E=T.height;(r.width!==A||r.height!==E)&&this.setSize(A,E)}return u===!1&&b.setRenderTarget(r),_=b.toneMapping,b.toneMapping=Jt,!0},this.hasRenderPass=function(){return u},this.end=function(b,T){b.toneMapping=_,d=!0;let A=r,E=a;for(let w=0;w<m.length;w++){let I=m[w];if(I.enabled!==!1&&(I.render(b,E,A,T),I.needsSwap!==!1)){let B=A;A=E,E=B}}if(f!==b.outputColorSpace||p!==b.toneMapping){f=b.outputColorSpace,p=b.toneMapping,c.defines={},ze.getTransfer(f)===Xe&&(c.defines.SRGB_TRANSFER="");let w=Jd[p];w&&(c.defines[w]=""),c.needsUpdate=!0}c.uniforms.tDiffuse.value=A.texture,b.setRenderTarget(y),b.render(l,h),y=null,d=!1},this.isCompositing=function(){return d},this.dispose=function(){r.dispose(),a.dispose(),o.dispose(),c.dispose()}}var rc=new At,xo=new Ln(1,1),ac=new ki,oc=new Vs,lc=new qi,kl=[],Gl=[],Hl=new Float32Array(16),Wl=new Float32Array(9),Xl=new Float32Array(4);function Ii(i,e,t){let n=i[0];if(n<=0||n>0)return i;let s=e*t,r=kl[s];if(r===void 0&&(r=new Float32Array(s),kl[s]=r),e!==0){n.toArray(r,0);for(let a=1,o=0;a!==e;++a)o+=t,i[a].toArray(r,o)}return r}function dt(i,e){if(i.length!==e.length)return!1;for(let t=0,n=i.length;t<n;t++)if(i[t]!==e[t])return!1;return!0}function ft(i,e){for(let t=0,n=e.length;t<n;t++)i[t]=e[t]}function ra(i,e){let t=Gl[e];t===void 0&&(t=new Int32Array(e),Gl[e]=t);for(let n=0;n!==e;++n)t[n]=i.allocateTextureUnit();return t}function Kd(i,e){let t=this.cache;t[0]!==e&&(i.uniform1f(this.addr,e),t[0]=e)}function Qd(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2f(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(dt(t,e))return;i.uniform2fv(this.addr,e),ft(t,e)}}function jd(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3f(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else if(e.r!==void 0)(t[0]!==e.r||t[1]!==e.g||t[2]!==e.b)&&(i.uniform3f(this.addr,e.r,e.g,e.b),t[0]=e.r,t[1]=e.g,t[2]=e.b);else{if(dt(t,e))return;i.uniform3fv(this.addr,e),ft(t,e)}}function ef(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4f(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(dt(t,e))return;i.uniform4fv(this.addr,e),ft(t,e)}}function tf(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(dt(t,e))return;i.uniformMatrix2fv(this.addr,!1,e),ft(t,e)}else{if(dt(t,n))return;Xl.set(n),i.uniformMatrix2fv(this.addr,!1,Xl),ft(t,n)}}function nf(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(dt(t,e))return;i.uniformMatrix3fv(this.addr,!1,e),ft(t,e)}else{if(dt(t,n))return;Wl.set(n),i.uniformMatrix3fv(this.addr,!1,Wl),ft(t,n)}}function sf(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(dt(t,e))return;i.uniformMatrix4fv(this.addr,!1,e),ft(t,e)}else{if(dt(t,n))return;Hl.set(n),i.uniformMatrix4fv(this.addr,!1,Hl),ft(t,n)}}function rf(i,e){let t=this.cache;t[0]!==e&&(i.uniform1i(this.addr,e),t[0]=e)}function af(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2i(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(dt(t,e))return;i.uniform2iv(this.addr,e),ft(t,e)}}function of(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3i(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(dt(t,e))return;i.uniform3iv(this.addr,e),ft(t,e)}}function lf(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4i(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(dt(t,e))return;i.uniform4iv(this.addr,e),ft(t,e)}}function cf(i,e){let t=this.cache;t[0]!==e&&(i.uniform1ui(this.addr,e),t[0]=e)}function hf(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2ui(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(dt(t,e))return;i.uniform2uiv(this.addr,e),ft(t,e)}}function uf(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3ui(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(dt(t,e))return;i.uniform3uiv(this.addr,e),ft(t,e)}}function df(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4ui(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(dt(t,e))return;i.uniform4uiv(this.addr,e),ft(t,e)}}function ff(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s);let r;this.type===i.SAMPLER_2D_SHADOW?(xo.compareFunction=t.isReversedDepthBuffer()?jr:Qr,r=xo):r=rc,t.setTexture2D(e||r,s)}function pf(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTexture3D(e||oc,s)}function mf(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTextureCube(e||lc,s)}function gf(i,e,t){let n=this.cache,s=t.allocateTextureUnit();n[0]!==s&&(i.uniform1i(this.addr,s),n[0]=s),t.setTexture2DArray(e||ac,s)}function _f(i){switch(i){case 5126:return Kd;case 35664:return Qd;case 35665:return jd;case 35666:return ef;case 35674:return tf;case 35675:return nf;case 35676:return sf;case 5124:case 35670:return rf;case 35667:case 35671:return af;case 35668:case 35672:return of;case 35669:case 35673:return lf;case 5125:return cf;case 36294:return hf;case 36295:return uf;case 36296:return df;case 35678:case 36198:case 36298:case 36306:case 35682:return ff;case 35679:case 36299:case 36307:return pf;case 35680:case 36300:case 36308:case 36293:return mf;case 36289:case 36303:case 36311:case 36292:return gf}}function xf(i,e){i.uniform1fv(this.addr,e)}function vf(i,e){let t=Ii(e,this.size,2);i.uniform2fv(this.addr,t)}function yf(i,e){let t=Ii(e,this.size,3);i.uniform3fv(this.addr,t)}function Mf(i,e){let t=Ii(e,this.size,4);i.uniform4fv(this.addr,t)}function Sf(i,e){let t=Ii(e,this.size,4);i.uniformMatrix2fv(this.addr,!1,t)}function bf(i,e){let t=Ii(e,this.size,9);i.uniformMatrix3fv(this.addr,!1,t)}function Af(i,e){let t=Ii(e,this.size,16);i.uniformMatrix4fv(this.addr,!1,t)}function Tf(i,e){i.uniform1iv(this.addr,e)}function Ef(i,e){i.uniform2iv(this.addr,e)}function wf(i,e){i.uniform3iv(this.addr,e)}function Cf(i,e){i.uniform4iv(this.addr,e)}function Rf(i,e){i.uniform1uiv(this.addr,e)}function If(i,e){i.uniform2uiv(this.addr,e)}function Pf(i,e){i.uniform3uiv(this.addr,e)}function Lf(i,e){i.uniform4uiv(this.addr,e)}function Df(i,e,t){let n=this.cache,s=e.length,r=ra(t,s);dt(n,r)||(i.uniform1iv(this.addr,r),ft(n,r));let a;this.type===i.SAMPLER_2D_SHADOW?a=xo:a=rc;for(let o=0;o!==s;++o)t.setTexture2D(e[o]||a,r[o])}function Uf(i,e,t){let n=this.cache,s=e.length,r=ra(t,s);dt(n,r)||(i.uniform1iv(this.addr,r),ft(n,r));for(let a=0;a!==s;++a)t.setTexture3D(e[a]||oc,r[a])}function Nf(i,e,t){let n=this.cache,s=e.length,r=ra(t,s);dt(n,r)||(i.uniform1iv(this.addr,r),ft(n,r));for(let a=0;a!==s;++a)t.setTextureCube(e[a]||lc,r[a])}function Ff(i,e,t){let n=this.cache,s=e.length,r=ra(t,s);dt(n,r)||(i.uniform1iv(this.addr,r),ft(n,r));for(let a=0;a!==s;++a)t.setTexture2DArray(e[a]||ac,r[a])}function Of(i){switch(i){case 5126:return xf;case 35664:return vf;case 35665:return yf;case 35666:return Mf;case 35674:return Sf;case 35675:return bf;case 35676:return Af;case 5124:case 35670:return Tf;case 35667:case 35671:return Ef;case 35668:case 35672:return wf;case 35669:case 35673:return Cf;case 5125:return Rf;case 36294:return If;case 36295:return Pf;case 36296:return Lf;case 35678:case 36198:case 36298:case 36306:case 35682:return Df;case 35679:case 36299:case 36307:return Uf;case 35680:case 36300:case 36308:case 36293:return Nf;case 36289:case 36303:case 36311:case 36292:return Ff}}var vo=class{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.setValue=_f(t.type)}},yo=class{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.size=t.size,this.setValue=Of(t.type)}},Mo=class{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,t,n){let s=this.seq;for(let r=0,a=s.length;r!==a;++r){let o=s[r];o.setValue(e,t[o.id],n)}}},go=/(\w+)(\])?(\[|\.)?/g;function ql(i,e){i.seq.push(e),i.map[e.id]=e}function Bf(i,e,t){let n=i.name,s=n.length;for(go.lastIndex=0;;){let r=go.exec(n),a=go.lastIndex,o=r[1],c=r[2]==="]",l=r[3];if(c&&(o=o|0),l===void 0||l==="["&&a+2===s){ql(t,l===void 0?new vo(o,i,e):new yo(o,i,e));break}else{let f=t.map[o];f===void 0&&(f=new Mo(o),ql(t,f)),t=f}}}var Ri=class{constructor(e,t){this.seq=[],this.map={};let n=e.getProgramParameter(t,e.ACTIVE_UNIFORMS);for(let a=0;a<n;++a){let o=e.getActiveUniform(t,a),c=e.getUniformLocation(t,o.name);Bf(o,c,this)}let s=[],r=[];for(let a of this.seq)a.type===e.SAMPLER_2D_SHADOW||a.type===e.SAMPLER_CUBE_SHADOW||a.type===e.SAMPLER_2D_ARRAY_SHADOW?s.push(a):r.push(a);s.length>0&&(this.seq=s.concat(r))}setValue(e,t,n,s){let r=this.map[t];r!==void 0&&r.setValue(e,n,s)}setOptional(e,t,n){let s=t[n];s!==void 0&&this.setValue(e,n,s)}static upload(e,t,n,s){for(let r=0,a=t.length;r!==a;++r){let o=t[r],c=n[o.id];c.needsUpdate!==!1&&o.setValue(e,c.value,s)}}static seqWithValue(e,t){let n=[];for(let s=0,r=e.length;s!==r;++s){let a=e[s];a.id in t&&n.push(a)}return n}};function Yl(i,e,t){let n=i.createShader(e);return i.shaderSource(n,t),i.compileShader(n),n}var zf=37297,Vf=0;function kf(i,e){let t=i.split(`
`),n=[],s=Math.max(e-6,0),r=Math.min(e+6,t.length);for(let a=s;a<r;a++){let o=a+1;n.push(`${o===e?">":" "} ${o}: ${t[a]}`)}return n.join(`
`)}var Zl=new Ie;function Gf(i){ze._getMatrix(Zl,ze.workingColorSpace,i);let e=`mat3( ${Zl.elements.map(t=>t.toFixed(4))} )`;switch(ze.getTransfer(i)){case Bi:return[e,"LinearTransferOETF"];case Xe:return[e,"sRGBTransferOETF"];default:return Ce("WebGLProgram: Unsupported color space: ",i),[e,"LinearTransferOETF"]}}function Jl(i,e,t){let n=i.getShaderParameter(e,i.COMPILE_STATUS),r=(i.getShaderInfoLog(e)||"").trim();if(n&&r==="")return"";let a=/ERROR: 0:(\d+)/.exec(r);if(a){let o=parseInt(a[1]);return t.toUpperCase()+`

`+r+`

`+kf(i.getShaderSource(e),o)}else return r}function Hf(i,e){let t=Gf(e);return[`vec4 ${i}( vec4 value ) {`,`	return ${t[1]}( vec4( value.rgb * ${t[0]}, value.a ) );`,"}"].join(`
`)}var Wf={[Ha]:"Linear",[Wa]:"Reinhard",[Xa]:"Cineon",[qa]:"ACESFilmic",[Za]:"AgX",[Ja]:"Neutral",[Ya]:"Custom"};function Xf(i,e){let t=Wf[e];return t===void 0?(Ce("WebGLProgram: Unsupported toneMapping:",e),"vec3 "+i+"( vec3 color ) { return LinearToneMapping( color ); }"):"vec3 "+i+"( vec3 color ) { return "+t+"ToneMapping( color ); }"}var ta=new F;function qf(){ze.getLuminanceCoefficients(ta);let i=ta.x.toFixed(4),e=ta.y.toFixed(4),t=ta.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${i}, ${e}, ${t} );`,"	return dot( weights, rgb );","}"].join(`
`)}function Yf(i){return[i.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",i.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(hs).join(`
`)}function Zf(i){let e=[];for(let t in i){let n=i[t];n!==!1&&e.push("#define "+t+" "+n)}return e.join(`
`)}function Jf(i,e){let t={},n=i.getProgramParameter(e,i.ACTIVE_ATTRIBUTES);for(let s=0;s<n;s++){let r=i.getActiveAttrib(e,s),a=r.name,o=1;r.type===i.FLOAT_MAT2&&(o=2),r.type===i.FLOAT_MAT3&&(o=3),r.type===i.FLOAT_MAT4&&(o=4),t[a]={type:r.type,location:i.getAttribLocation(e,a),locationSize:o}}return t}function hs(i){return i!==""}function $l(i,e){let t=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return i.replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,t).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function Kl(i,e){return i.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}var $f=/^[ \t]*#include +<([\w\d./]+)>/gm;function So(i){return i.replace($f,Qf)}var Kf=new Map;function Qf(i,e){let t=Le[e];if(t===void 0){let n=Kf.get(e);if(n!==void 0)t=Le[n],Ce('WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,n);else throw new Error("Can not resolve #include <"+e+">")}return So(t)}var jf=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function Ql(i){return i.replace(jf,ep)}function ep(i,e,t,n){let s="";for(let r=parseInt(e);r<parseInt(t);r++)s+=n.replace(/\[\s*i\s*\]/g,"[ "+r+" ]").replace(/UNROLLED_LOOP_INDEX/g,r);return s}function jl(i){let e=`precision ${i.precision} float;
	precision ${i.precision} int;
	precision ${i.precision} sampler2D;
	precision ${i.precision} samplerCube;
	precision ${i.precision} sampler3D;
	precision ${i.precision} sampler2DArray;
	precision ${i.precision} sampler2DShadow;
	precision ${i.precision} samplerCubeShadow;
	precision ${i.precision} sampler2DArrayShadow;
	precision ${i.precision} isampler2D;
	precision ${i.precision} isampler3D;
	precision ${i.precision} isamplerCube;
	precision ${i.precision} isampler2DArray;
	precision ${i.precision} usampler2D;
	precision ${i.precision} usampler3D;
	precision ${i.precision} usamplerCube;
	precision ${i.precision} usampler2DArray;
	`;return i.precision==="highp"?e+=`
#define HIGH_PRECISION`:i.precision==="mediump"?e+=`
#define MEDIUM_PRECISION`:i.precision==="lowp"&&(e+=`
#define LOW_PRECISION`),e}var tp={[es]:"SHADOWMAP_TYPE_PCF",[Ti]:"SHADOWMAP_TYPE_VSM"};function np(i){return tp[i.shadowMapType]||"SHADOWMAP_TYPE_BASIC"}var ip={[Nn]:"ENVMAP_TYPE_CUBE",[jn]:"ENVMAP_TYPE_CUBE",[ts]:"ENVMAP_TYPE_CUBE_UV"};function sp(i){return i.envMap===!1?"ENVMAP_TYPE_CUBE":ip[i.envMapMode]||"ENVMAP_TYPE_CUBE"}var rp={[jn]:"ENVMAP_MODE_REFRACTION"};function ap(i){return i.envMap===!1?"ENVMAP_MODE_REFLECTION":rp[i.envMapMode]||"ENVMAP_MODE_REFLECTION"}var op={[Ga]:"ENVMAP_BLENDING_MULTIPLY",[vl]:"ENVMAP_BLENDING_MIX",[yl]:"ENVMAP_BLENDING_ADD"};function lp(i){return i.envMap===!1?"ENVMAP_BLENDING_NONE":op[i.combine]||"ENVMAP_BLENDING_NONE"}function cp(i){let e=i.envMapCubeUVHeight;if(e===null)return null;let t=Math.log2(e)-2,n=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,t),112)),texelHeight:n,maxMip:t}}function hp(i,e,t,n){let s=i.getContext(),r=t.defines,a=t.vertexShader,o=t.fragmentShader,c=np(t),l=sp(t),h=ap(t),f=lp(t),p=cp(t),d=Yf(t),_=Zf(r),y=s.createProgram(),m,u,b=t.glslVersion?"#version "+t.glslVersion+`
`:"";t.isRawShaderMaterial?(m=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,_].filter(hs).join(`
`),m.length>0&&(m+=`
`),u=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,_].filter(hs).join(`
`),u.length>0&&(u+=`
`)):(m=[jl(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,_,t.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",t.batching?"#define USE_BATCHING":"",t.batchingColor?"#define USE_BATCHING_COLOR":"",t.instancing?"#define USE_INSTANCING":"",t.instancingColor?"#define USE_INSTANCING_COLOR":"",t.instancingMorph?"#define USE_INSTANCING_MORPH":"",t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.map?"#define USE_MAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+h:"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.displacementMap?"#define USE_DISPLACEMENTMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.mapUv?"#define MAP_UV "+t.mapUv:"",t.alphaMapUv?"#define ALPHAMAP_UV "+t.alphaMapUv:"",t.lightMapUv?"#define LIGHTMAP_UV "+t.lightMapUv:"",t.aoMapUv?"#define AOMAP_UV "+t.aoMapUv:"",t.emissiveMapUv?"#define EMISSIVEMAP_UV "+t.emissiveMapUv:"",t.bumpMapUv?"#define BUMPMAP_UV "+t.bumpMapUv:"",t.normalMapUv?"#define NORMALMAP_UV "+t.normalMapUv:"",t.displacementMapUv?"#define DISPLACEMENTMAP_UV "+t.displacementMapUv:"",t.metalnessMapUv?"#define METALNESSMAP_UV "+t.metalnessMapUv:"",t.roughnessMapUv?"#define ROUGHNESSMAP_UV "+t.roughnessMapUv:"",t.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+t.anisotropyMapUv:"",t.clearcoatMapUv?"#define CLEARCOATMAP_UV "+t.clearcoatMapUv:"",t.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+t.clearcoatNormalMapUv:"",t.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+t.clearcoatRoughnessMapUv:"",t.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+t.iridescenceMapUv:"",t.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+t.iridescenceThicknessMapUv:"",t.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+t.sheenColorMapUv:"",t.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+t.sheenRoughnessMapUv:"",t.specularMapUv?"#define SPECULARMAP_UV "+t.specularMapUv:"",t.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+t.specularColorMapUv:"",t.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+t.specularIntensityMapUv:"",t.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+t.transmissionMapUv:"",t.thicknessMapUv?"#define THICKNESSMAP_UV "+t.thicknessMapUv:"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.flatShading?"#define FLAT_SHADED":"",t.skinning?"#define USE_SKINNING":"",t.morphTargets?"#define USE_MORPHTARGETS":"",t.morphNormals&&t.flatShading===!1?"#define USE_MORPHNORMALS":"",t.morphColors?"#define USE_MORPHCOLORS":"",t.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+t.morphTextureStride:"",t.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+t.morphTargetsCount:"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+c:"",t.sizeAttenuation?"#define USE_SIZEATTENUATION":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(hs).join(`
`),u=[jl(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,_,t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",t.map?"#define USE_MAP":"",t.matcap?"#define USE_MATCAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+l:"",t.envMap?"#define "+h:"",t.envMap?"#define "+f:"",p?"#define CUBEUV_TEXEL_WIDTH "+p.texelWidth:"",p?"#define CUBEUV_TEXEL_HEIGHT "+p.texelHeight:"",p?"#define CUBEUV_MAX_MIP "+p.maxMip+".0":"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoat?"#define USE_CLEARCOAT":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.dispersion?"#define USE_DISPERSION":"",t.iridescence?"#define USE_IRIDESCENCE":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaTest?"#define USE_ALPHATEST":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.sheen?"#define USE_SHEEN":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors||t.instancingColor||t.batchingColor?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.gradientMap?"#define USE_GRADIENTMAP":"",t.flatShading?"#define FLAT_SHADED":"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+c:"",t.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",t.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",t.toneMapping!==Jt?"#define TONE_MAPPING":"",t.toneMapping!==Jt?Le.tonemapping_pars_fragment:"",t.toneMapping!==Jt?Xf("toneMapping",t.toneMapping):"",t.dithering?"#define DITHERING":"",t.opaque?"#define OPAQUE":"",Le.colorspace_pars_fragment,Hf("linearToOutputTexel",t.outputColorSpace),qf(),t.useDepthPacking?"#define DEPTH_PACKING "+t.depthPacking:"",`
`].filter(hs).join(`
`)),a=So(a),a=$l(a,t),a=Kl(a,t),o=So(o),o=$l(o,t),o=Kl(o,t),a=Ql(a),o=Ql(o),t.isRawShaderMaterial!==!0&&(b=`#version 300 es
`,m=[d,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+m,u=["#define varying in",t.glslVersion===so?"":"layout(location = 0) out highp vec4 pc_fragColor;",t.glslVersion===so?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+u);let T=b+m+a,A=b+u+o,E=Yl(s,s.VERTEX_SHADER,T),w=Yl(s,s.FRAGMENT_SHADER,A);s.attachShader(y,E),s.attachShader(y,w),t.index0AttributeName!==void 0?s.bindAttribLocation(y,0,t.index0AttributeName):t.morphTargets===!0&&s.bindAttribLocation(y,0,"position"),s.linkProgram(y);function I(L){if(i.debug.checkShaderErrors){let V=s.getProgramInfoLog(y)||"",z=s.getShaderInfoLog(E)||"",W=s.getShaderInfoLog(w)||"",Y=V.trim(),k=z.trim(),H=W.trim(),$=!0,he=!0;if(s.getProgramParameter(y,s.LINK_STATUS)===!1)if($=!1,typeof i.debug.onShaderError=="function")i.debug.onShaderError(s,y,E,w);else{let ae=Jl(s,E,"vertex"),ue=Jl(s,w,"fragment");Ee("THREE.WebGLProgram: Shader Error "+s.getError()+" - VALIDATE_STATUS "+s.getProgramParameter(y,s.VALIDATE_STATUS)+`

Material Name: `+L.name+`
Material Type: `+L.type+`

Program Info Log: `+Y+`
`+ae+`
`+ue)}else Y!==""?Ce("WebGLProgram: Program Info Log:",Y):(k===""||H==="")&&(he=!1);he&&(L.diagnostics={runnable:$,programLog:Y,vertexShader:{log:k,prefix:m},fragmentShader:{log:H,prefix:u}})}s.deleteShader(E),s.deleteShader(w),B=new Ri(s,y),v=Jf(s,y)}let B;this.getUniforms=function(){return B===void 0&&I(this),B};let v;this.getAttributes=function(){return v===void 0&&I(this),v};let M=t.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return M===!1&&(M=s.getProgramParameter(y,zf)),M},this.destroy=function(){n.releaseStatesOfProgram(this),s.deleteProgram(y),this.program=void 0},this.type=t.shaderType,this.name=t.shaderName,this.id=Vf++,this.cacheKey=e,this.usedTimes=1,this.program=y,this.vertexShader=E,this.fragmentShader=w,this}var up=0,bo=class{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e){let t=e.vertexShader,n=e.fragmentShader,s=this._getShaderStage(t),r=this._getShaderStage(n),a=this._getShaderCacheForMaterial(e);return a.has(s)===!1&&(a.add(s),s.usedTimes++),a.has(r)===!1&&(a.add(r),r.usedTimes++),this}remove(e){let t=this.materialCache.get(e);for(let n of t)n.usedTimes--,n.usedTimes===0&&this.shaderCache.delete(n.code);return this.materialCache.delete(e),this}getVertexShaderID(e){return this._getShaderStage(e.vertexShader).id}getFragmentShaderID(e){return this._getShaderStage(e.fragmentShader).id}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){let t=this.materialCache,n=t.get(e);return n===void 0&&(n=new Set,t.set(e,n)),n}_getShaderStage(e){let t=this.shaderCache,n=t.get(e);return n===void 0&&(n=new Ao(e),t.set(e,n)),n}},Ao=class{constructor(e){this.id=up++,this.code=e,this.usedTimes=0}};function dp(i,e,t,n,s,r,a){let o=new Gi,c=new bo,l=new Set,h=[],f=new Map,p=s.logarithmicDepthBuffer,d=s.precision,_={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distance",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function y(v){return l.add(v),v===0?"uv":`uv${v}`}function m(v,M,L,V,z){let W=V.fog,Y=z.geometry,k=v.isMeshStandardMaterial?V.environment:null,H=(v.isMeshStandardMaterial?t:e).get(v.envMap||k),$=H&&H.mapping===ts?H.image.height:null,he=_[v.type];v.precision!==null&&(d=s.getMaxPrecision(v.precision),d!==v.precision&&Ce("WebGLProgram.getParameters:",v.precision,"not supported, using",d,"instead."));let ae=Y.morphAttributes.position||Y.morphAttributes.normal||Y.morphAttributes.color,ue=ae!==void 0?ae.length:0,Fe=0;Y.morphAttributes.position!==void 0&&(Fe=1),Y.morphAttributes.normal!==void 0&&(Fe=2),Y.morphAttributes.color!==void 0&&(Fe=3);let De,st,nt,q;if(he){let Ye=cn[he];De=Ye.vertexShader,st=Ye.fragmentShader}else De=v.vertexShader,st=v.fragmentShader,c.update(v),nt=c.getVertexShaderID(v),q=c.getFragmentShaderID(v);let K=i.getRenderTarget(),pe=i.state.buffers.depth.getReversed(),Pe=z.isInstancedMesh===!0,_e=z.isBatchedMesh===!0,ke=!!v.map,pt=!!v.matcap,Ve=!!H,qe=!!v.aoMap,Ke=!!v.lightMap,Ue=!!v.bumpMap,lt=!!v.normalMap,C=!!v.displacementMap,ct=!!v.emissiveMap,We=!!v.metalnessMap,je=!!v.roughnessMap,ve=v.anisotropy>0,S=v.clearcoat>0,g=v.dispersion>0,P=v.iridescence>0,X=v.sheen>0,J=v.transmission>0,G=ve&&!!v.anisotropyMap,Me=S&&!!v.clearcoatMap,ne=S&&!!v.clearcoatNormalMap,xe=S&&!!v.clearcoatRoughnessMap,we=P&&!!v.iridescenceMap,j=P&&!!v.iridescenceThicknessMap,se=X&&!!v.sheenColorMap,ge=X&&!!v.sheenRoughnessMap,ye=!!v.specularMap,ie=!!v.specularColorMap,Ne=!!v.specularIntensityMap,R=J&&!!v.transmissionMap,ce=J&&!!v.thicknessMap,ee=!!v.gradientMap,de=!!v.alphaMap,Q=v.alphaTest>0,Z=!!v.alphaHash,te=!!v.extensions,Re=Jt;v.toneMapped&&(K===null||K.isXRRenderTarget===!0)&&(Re=i.toneMapping);let et={shaderID:he,shaderType:v.type,shaderName:v.name,vertexShader:De,fragmentShader:st,defines:v.defines,customVertexShaderID:nt,customFragmentShaderID:q,isRawShaderMaterial:v.isRawShaderMaterial===!0,glslVersion:v.glslVersion,precision:d,batching:_e,batchingColor:_e&&z._colorsTexture!==null,instancing:Pe,instancingColor:Pe&&z.instanceColor!==null,instancingMorph:Pe&&z.morphTexture!==null,outputColorSpace:K===null?i.outputColorSpace:K.isXRRenderTarget===!0?K.texture.colorSpace:Zn,alphaToCoverage:!!v.alphaToCoverage,map:ke,matcap:pt,envMap:Ve,envMapMode:Ve&&H.mapping,envMapCubeUVHeight:$,aoMap:qe,lightMap:Ke,bumpMap:Ue,normalMap:lt,displacementMap:C,emissiveMap:ct,normalMapObjectSpace:lt&&v.normalMapType===Al,normalMapTangentSpace:lt&&v.normalMapType===bl,metalnessMap:We,roughnessMap:je,anisotropy:ve,anisotropyMap:G,clearcoat:S,clearcoatMap:Me,clearcoatNormalMap:ne,clearcoatRoughnessMap:xe,dispersion:g,iridescence:P,iridescenceMap:we,iridescenceThicknessMap:j,sheen:X,sheenColorMap:se,sheenRoughnessMap:ge,specularMap:ye,specularColorMap:ie,specularIntensityMap:Ne,transmission:J,transmissionMap:R,thicknessMap:ce,gradientMap:ee,opaque:v.transparent===!1&&v.blending===qn&&v.alphaToCoverage===!1,alphaMap:de,alphaTest:Q,alphaHash:Z,combine:v.combine,mapUv:ke&&y(v.map.channel),aoMapUv:qe&&y(v.aoMap.channel),lightMapUv:Ke&&y(v.lightMap.channel),bumpMapUv:Ue&&y(v.bumpMap.channel),normalMapUv:lt&&y(v.normalMap.channel),displacementMapUv:C&&y(v.displacementMap.channel),emissiveMapUv:ct&&y(v.emissiveMap.channel),metalnessMapUv:We&&y(v.metalnessMap.channel),roughnessMapUv:je&&y(v.roughnessMap.channel),anisotropyMapUv:G&&y(v.anisotropyMap.channel),clearcoatMapUv:Me&&y(v.clearcoatMap.channel),clearcoatNormalMapUv:ne&&y(v.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:xe&&y(v.clearcoatRoughnessMap.channel),iridescenceMapUv:we&&y(v.iridescenceMap.channel),iridescenceThicknessMapUv:j&&y(v.iridescenceThicknessMap.channel),sheenColorMapUv:se&&y(v.sheenColorMap.channel),sheenRoughnessMapUv:ge&&y(v.sheenRoughnessMap.channel),specularMapUv:ye&&y(v.specularMap.channel),specularColorMapUv:ie&&y(v.specularColorMap.channel),specularIntensityMapUv:Ne&&y(v.specularIntensityMap.channel),transmissionMapUv:R&&y(v.transmissionMap.channel),thicknessMapUv:ce&&y(v.thicknessMap.channel),alphaMapUv:de&&y(v.alphaMap.channel),vertexTangents:!!Y.attributes.tangent&&(lt||ve),vertexColors:v.vertexColors,vertexAlphas:v.vertexColors===!0&&!!Y.attributes.color&&Y.attributes.color.itemSize===4,pointsUvs:z.isPoints===!0&&!!Y.attributes.uv&&(ke||de),fog:!!W,useFog:v.fog===!0,fogExp2:!!W&&W.isFogExp2,flatShading:v.flatShading===!0&&v.wireframe===!1,sizeAttenuation:v.sizeAttenuation===!0,logarithmicDepthBuffer:p,reversedDepthBuffer:pe,skinning:z.isSkinnedMesh===!0,morphTargets:Y.morphAttributes.position!==void 0,morphNormals:Y.morphAttributes.normal!==void 0,morphColors:Y.morphAttributes.color!==void 0,morphTargetsCount:ue,morphTextureStride:Fe,numDirLights:M.directional.length,numPointLights:M.point.length,numSpotLights:M.spot.length,numSpotLightMaps:M.spotLightMap.length,numRectAreaLights:M.rectArea.length,numHemiLights:M.hemi.length,numDirLightShadows:M.directionalShadowMap.length,numPointLightShadows:M.pointShadowMap.length,numSpotLightShadows:M.spotShadowMap.length,numSpotLightShadowsWithMaps:M.numSpotLightShadowsWithMaps,numLightProbes:M.numLightProbes,numClippingPlanes:a.numPlanes,numClipIntersection:a.numIntersection,dithering:v.dithering,shadowMapEnabled:i.shadowMap.enabled&&L.length>0,shadowMapType:i.shadowMap.type,toneMapping:Re,decodeVideoTexture:ke&&v.map.isVideoTexture===!0&&ze.getTransfer(v.map.colorSpace)===Xe,decodeVideoTextureEmissive:ct&&v.emissiveMap.isVideoTexture===!0&&ze.getTransfer(v.emissiveMap.colorSpace)===Xe,premultipliedAlpha:v.premultipliedAlpha,doubleSided:v.side===rn,flipSided:v.side===Tt,useDepthPacking:v.depthPacking>=0,depthPacking:v.depthPacking||0,index0AttributeName:v.index0AttributeName,extensionClipCullDistance:te&&v.extensions.clipCullDistance===!0&&n.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(te&&v.extensions.multiDraw===!0||_e)&&n.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:n.has("KHR_parallel_shader_compile"),customProgramCacheKey:v.customProgramCacheKey()};return et.vertexUv1s=l.has(1),et.vertexUv2s=l.has(2),et.vertexUv3s=l.has(3),l.clear(),et}function u(v){let M=[];if(v.shaderID?M.push(v.shaderID):(M.push(v.customVertexShaderID),M.push(v.customFragmentShaderID)),v.defines!==void 0)for(let L in v.defines)M.push(L),M.push(v.defines[L]);return v.isRawShaderMaterial===!1&&(b(M,v),T(M,v),M.push(i.outputColorSpace)),M.push(v.customProgramCacheKey),M.join()}function b(v,M){v.push(M.precision),v.push(M.outputColorSpace),v.push(M.envMapMode),v.push(M.envMapCubeUVHeight),v.push(M.mapUv),v.push(M.alphaMapUv),v.push(M.lightMapUv),v.push(M.aoMapUv),v.push(M.bumpMapUv),v.push(M.normalMapUv),v.push(M.displacementMapUv),v.push(M.emissiveMapUv),v.push(M.metalnessMapUv),v.push(M.roughnessMapUv),v.push(M.anisotropyMapUv),v.push(M.clearcoatMapUv),v.push(M.clearcoatNormalMapUv),v.push(M.clearcoatRoughnessMapUv),v.push(M.iridescenceMapUv),v.push(M.iridescenceThicknessMapUv),v.push(M.sheenColorMapUv),v.push(M.sheenRoughnessMapUv),v.push(M.specularMapUv),v.push(M.specularColorMapUv),v.push(M.specularIntensityMapUv),v.push(M.transmissionMapUv),v.push(M.thicknessMapUv),v.push(M.combine),v.push(M.fogExp2),v.push(M.sizeAttenuation),v.push(M.morphTargetsCount),v.push(M.morphAttributeCount),v.push(M.numDirLights),v.push(M.numPointLights),v.push(M.numSpotLights),v.push(M.numSpotLightMaps),v.push(M.numHemiLights),v.push(M.numRectAreaLights),v.push(M.numDirLightShadows),v.push(M.numPointLightShadows),v.push(M.numSpotLightShadows),v.push(M.numSpotLightShadowsWithMaps),v.push(M.numLightProbes),v.push(M.shadowMapType),v.push(M.toneMapping),v.push(M.numClippingPlanes),v.push(M.numClipIntersection),v.push(M.depthPacking)}function T(v,M){o.disableAll(),M.instancing&&o.enable(0),M.instancingColor&&o.enable(1),M.instancingMorph&&o.enable(2),M.matcap&&o.enable(3),M.envMap&&o.enable(4),M.normalMapObjectSpace&&o.enable(5),M.normalMapTangentSpace&&o.enable(6),M.clearcoat&&o.enable(7),M.iridescence&&o.enable(8),M.alphaTest&&o.enable(9),M.vertexColors&&o.enable(10),M.vertexAlphas&&o.enable(11),M.vertexUv1s&&o.enable(12),M.vertexUv2s&&o.enable(13),M.vertexUv3s&&o.enable(14),M.vertexTangents&&o.enable(15),M.anisotropy&&o.enable(16),M.alphaHash&&o.enable(17),M.batching&&o.enable(18),M.dispersion&&o.enable(19),M.batchingColor&&o.enable(20),M.gradientMap&&o.enable(21),v.push(o.mask),o.disableAll(),M.fog&&o.enable(0),M.useFog&&o.enable(1),M.flatShading&&o.enable(2),M.logarithmicDepthBuffer&&o.enable(3),M.reversedDepthBuffer&&o.enable(4),M.skinning&&o.enable(5),M.morphTargets&&o.enable(6),M.morphNormals&&o.enable(7),M.morphColors&&o.enable(8),M.premultipliedAlpha&&o.enable(9),M.shadowMapEnabled&&o.enable(10),M.doubleSided&&o.enable(11),M.flipSided&&o.enable(12),M.useDepthPacking&&o.enable(13),M.dithering&&o.enable(14),M.transmission&&o.enable(15),M.sheen&&o.enable(16),M.opaque&&o.enable(17),M.pointsUvs&&o.enable(18),M.decodeVideoTexture&&o.enable(19),M.decodeVideoTextureEmissive&&o.enable(20),M.alphaToCoverage&&o.enable(21),v.push(o.mask)}function A(v){let M=_[v.type],L;if(M){let V=cn[M];L=Ul.clone(V.uniforms)}else L=v.uniforms;return L}function E(v,M){let L=f.get(M);return L!==void 0?++L.usedTimes:(L=new hp(i,M,v,r),h.push(L),f.set(M,L)),L}function w(v){if(--v.usedTimes===0){let M=h.indexOf(v);h[M]=h[h.length-1],h.pop(),f.delete(v.cacheKey),v.destroy()}}function I(v){c.remove(v)}function B(){c.dispose()}return{getParameters:m,getProgramCacheKey:u,getUniforms:A,acquireProgram:E,releaseProgram:w,releaseShaderCache:I,programs:h,dispose:B}}function fp(){let i=new WeakMap;function e(a){return i.has(a)}function t(a){let o=i.get(a);return o===void 0&&(o={},i.set(a,o)),o}function n(a){i.delete(a)}function s(a,o,c){i.get(a)[o]=c}function r(){i=new WeakMap}return{has:e,get:t,remove:n,update:s,dispose:r}}function pp(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.material.id!==e.material.id?i.material.id-e.material.id:i.z!==e.z?i.z-e.z:i.id-e.id}function ec(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.z!==e.z?e.z-i.z:i.id-e.id}function tc(){let i=[],e=0,t=[],n=[],s=[];function r(){e=0,t.length=0,n.length=0,s.length=0}function a(f,p,d,_,y,m){let u=i[e];return u===void 0?(u={id:f.id,object:f,geometry:p,material:d,groupOrder:_,renderOrder:f.renderOrder,z:y,group:m},i[e]=u):(u.id=f.id,u.object=f,u.geometry=p,u.material=d,u.groupOrder=_,u.renderOrder=f.renderOrder,u.z=y,u.group=m),e++,u}function o(f,p,d,_,y,m){let u=a(f,p,d,_,y,m);d.transmission>0?n.push(u):d.transparent===!0?s.push(u):t.push(u)}function c(f,p,d,_,y,m){let u=a(f,p,d,_,y,m);d.transmission>0?n.unshift(u):d.transparent===!0?s.unshift(u):t.unshift(u)}function l(f,p){t.length>1&&t.sort(f||pp),n.length>1&&n.sort(p||ec),s.length>1&&s.sort(p||ec)}function h(){for(let f=e,p=i.length;f<p;f++){let d=i[f];if(d.id===null)break;d.id=null,d.object=null,d.geometry=null,d.material=null,d.group=null}}return{opaque:t,transmissive:n,transparent:s,init:r,push:o,unshift:c,finish:h,sort:l}}function mp(){let i=new WeakMap;function e(n,s){let r=i.get(n),a;return r===void 0?(a=new tc,i.set(n,[a])):s>=r.length?(a=new tc,r.push(a)):a=r[s],a}function t(){i=new WeakMap}return{get:e,dispose:t}}function gp(){let i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"DirectionalLight":t={direction:new F,color:new He};break;case"SpotLight":t={position:new F,direction:new F,color:new He,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":t={position:new F,color:new He,distance:0,decay:0};break;case"HemisphereLight":t={direction:new F,skyColor:new He,groundColor:new He};break;case"RectAreaLight":t={color:new He,position:new F,halfWidth:new F,halfHeight:new F};break}return i[e.id]=t,t}}}function _p(){let i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"DirectionalLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Je};break;case"SpotLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Je};break;case"PointLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new Je,shadowCameraNear:1,shadowCameraFar:1e3};break}return i[e.id]=t,t}}}var xp=0;function vp(i,e){return(e.castShadow?2:0)-(i.castShadow?2:0)+(e.map?1:0)-(i.map?1:0)}function yp(i){let e=new gp,t=_p(),n={version:0,hash:{directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let l=0;l<9;l++)n.probe.push(new F);let s=new F,r=new ut,a=new ut;function o(l){let h=0,f=0,p=0;for(let v=0;v<9;v++)n.probe[v].set(0,0,0);let d=0,_=0,y=0,m=0,u=0,b=0,T=0,A=0,E=0,w=0,I=0;l.sort(vp);for(let v=0,M=l.length;v<M;v++){let L=l[v],V=L.color,z=L.intensity,W=L.distance,Y=null;if(L.shadow&&L.shadow.map&&(L.shadow.map.texture.format===ei?Y=L.shadow.map.texture:Y=L.shadow.map.depthTexture||L.shadow.map.texture),L.isAmbientLight)h+=V.r*z,f+=V.g*z,p+=V.b*z;else if(L.isLightProbe){for(let k=0;k<9;k++)n.probe[k].addScaledVector(L.sh.coefficients[k],z);I++}else if(L.isDirectionalLight){let k=e.get(L);if(k.color.copy(L.color).multiplyScalar(L.intensity),L.castShadow){let H=L.shadow,$=t.get(L);$.shadowIntensity=H.intensity,$.shadowBias=H.bias,$.shadowNormalBias=H.normalBias,$.shadowRadius=H.radius,$.shadowMapSize=H.mapSize,n.directionalShadow[d]=$,n.directionalShadowMap[d]=Y,n.directionalShadowMatrix[d]=L.shadow.matrix,b++}n.directional[d]=k,d++}else if(L.isSpotLight){let k=e.get(L);k.position.setFromMatrixPosition(L.matrixWorld),k.color.copy(V).multiplyScalar(z),k.distance=W,k.coneCos=Math.cos(L.angle),k.penumbraCos=Math.cos(L.angle*(1-L.penumbra)),k.decay=L.decay,n.spot[y]=k;let H=L.shadow;if(L.map&&(n.spotLightMap[E]=L.map,E++,H.updateMatrices(L),L.castShadow&&w++),n.spotLightMatrix[y]=H.matrix,L.castShadow){let $=t.get(L);$.shadowIntensity=H.intensity,$.shadowBias=H.bias,$.shadowNormalBias=H.normalBias,$.shadowRadius=H.radius,$.shadowMapSize=H.mapSize,n.spotShadow[y]=$,n.spotShadowMap[y]=Y,A++}y++}else if(L.isRectAreaLight){let k=e.get(L);k.color.copy(V).multiplyScalar(z),k.halfWidth.set(L.width*.5,0,0),k.halfHeight.set(0,L.height*.5,0),n.rectArea[m]=k,m++}else if(L.isPointLight){let k=e.get(L);if(k.color.copy(L.color).multiplyScalar(L.intensity),k.distance=L.distance,k.decay=L.decay,L.castShadow){let H=L.shadow,$=t.get(L);$.shadowIntensity=H.intensity,$.shadowBias=H.bias,$.shadowNormalBias=H.normalBias,$.shadowRadius=H.radius,$.shadowMapSize=H.mapSize,$.shadowCameraNear=H.camera.near,$.shadowCameraFar=H.camera.far,n.pointShadow[_]=$,n.pointShadowMap[_]=Y,n.pointShadowMatrix[_]=L.shadow.matrix,T++}n.point[_]=k,_++}else if(L.isHemisphereLight){let k=e.get(L);k.skyColor.copy(L.color).multiplyScalar(z),k.groundColor.copy(L.groundColor).multiplyScalar(z),n.hemi[u]=k,u++}}m>0&&(i.has("OES_texture_float_linear")===!0?(n.rectAreaLTC1=oe.LTC_FLOAT_1,n.rectAreaLTC2=oe.LTC_FLOAT_2):(n.rectAreaLTC1=oe.LTC_HALF_1,n.rectAreaLTC2=oe.LTC_HALF_2)),n.ambient[0]=h,n.ambient[1]=f,n.ambient[2]=p;let B=n.hash;(B.directionalLength!==d||B.pointLength!==_||B.spotLength!==y||B.rectAreaLength!==m||B.hemiLength!==u||B.numDirectionalShadows!==b||B.numPointShadows!==T||B.numSpotShadows!==A||B.numSpotMaps!==E||B.numLightProbes!==I)&&(n.directional.length=d,n.spot.length=y,n.rectArea.length=m,n.point.length=_,n.hemi.length=u,n.directionalShadow.length=b,n.directionalShadowMap.length=b,n.pointShadow.length=T,n.pointShadowMap.length=T,n.spotShadow.length=A,n.spotShadowMap.length=A,n.directionalShadowMatrix.length=b,n.pointShadowMatrix.length=T,n.spotLightMatrix.length=A+E-w,n.spotLightMap.length=E,n.numSpotLightShadowsWithMaps=w,n.numLightProbes=I,B.directionalLength=d,B.pointLength=_,B.spotLength=y,B.rectAreaLength=m,B.hemiLength=u,B.numDirectionalShadows=b,B.numPointShadows=T,B.numSpotShadows=A,B.numSpotMaps=E,B.numLightProbes=I,n.version=xp++)}function c(l,h){let f=0,p=0,d=0,_=0,y=0,m=h.matrixWorldInverse;for(let u=0,b=l.length;u<b;u++){let T=l[u];if(T.isDirectionalLight){let A=n.directional[f];A.direction.setFromMatrixPosition(T.matrixWorld),s.setFromMatrixPosition(T.target.matrixWorld),A.direction.sub(s),A.direction.transformDirection(m),f++}else if(T.isSpotLight){let A=n.spot[d];A.position.setFromMatrixPosition(T.matrixWorld),A.position.applyMatrix4(m),A.direction.setFromMatrixPosition(T.matrixWorld),s.setFromMatrixPosition(T.target.matrixWorld),A.direction.sub(s),A.direction.transformDirection(m),d++}else if(T.isRectAreaLight){let A=n.rectArea[_];A.position.setFromMatrixPosition(T.matrixWorld),A.position.applyMatrix4(m),a.identity(),r.copy(T.matrixWorld),r.premultiply(m),a.extractRotation(r),A.halfWidth.set(T.width*.5,0,0),A.halfHeight.set(0,T.height*.5,0),A.halfWidth.applyMatrix4(a),A.halfHeight.applyMatrix4(a),_++}else if(T.isPointLight){let A=n.point[p];A.position.setFromMatrixPosition(T.matrixWorld),A.position.applyMatrix4(m),p++}else if(T.isHemisphereLight){let A=n.hemi[y];A.direction.setFromMatrixPosition(T.matrixWorld),A.direction.transformDirection(m),y++}}}return{setup:o,setupView:c,state:n}}function nc(i){let e=new yp(i),t=[],n=[];function s(h){l.camera=h,t.length=0,n.length=0}function r(h){t.push(h)}function a(h){n.push(h)}function o(){e.setup(t)}function c(h){e.setupView(t,h)}let l={lightsArray:t,shadowsArray:n,camera:null,lights:e,transmissionRenderTarget:{}};return{init:s,state:l,setupLights:o,setupLightsView:c,pushLight:r,pushShadow:a}}function Mp(i){let e=new WeakMap;function t(s,r=0){let a=e.get(s),o;return a===void 0?(o=new nc(i),e.set(s,[o])):r>=a.length?(o=new nc(i),a.push(o)):o=a[r],o}function n(){e=new WeakMap}return{get:t,dispose:n}}var Sp=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,bp=`uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ).rg;
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ).r;
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( max( 0.0, squared_mean - mean * mean ) );
	gl_FragColor = vec4( mean, std_dev, 0.0, 1.0 );
}`,Ap=[new F(1,0,0),new F(-1,0,0),new F(0,1,0),new F(0,-1,0),new F(0,0,1),new F(0,0,-1)],Tp=[new F(0,-1,0),new F(0,-1,0),new F(0,0,1),new F(0,0,-1),new F(0,-1,0),new F(0,-1,0)],ic=new ut,cs=new F,_o=new F;function Ep(i,e,t){let n=new Ji,s=new Je,r=new Je,a=new ot,o=new qs,c=new Ys,l={},h=t.maxTextureSize,f={[xn]:Tt,[Tt]:xn,[rn]:rn},p=new Ft({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new Je},radius:{value:4}},vertexShader:Sp,fragmentShader:bp}),d=p.clone();d.defines.HORIZONTAL_PASS=1;let _=new sn;_.setAttribute("position",new Ut(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));let y=new Rt(_,p),m=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=es;let u=this.type;this.render=function(w,I,B){if(m.enabled===!1||m.autoUpdate===!1&&m.needsUpdate===!1||w.length===0)return;w.type===el&&(Ce("WebGLShadowMap: PCFSoftShadowMap has been deprecated. Using PCFShadowMap instead."),w.type=es);let v=i.getRenderTarget(),M=i.getActiveCubeFace(),L=i.getActiveMipmapLevel(),V=i.state;V.setBlending(an),V.buffers.depth.getReversed()===!0?V.buffers.color.setClear(0,0,0,0):V.buffers.color.setClear(1,1,1,1),V.buffers.depth.setTest(!0),V.setScissorTest(!1);let z=u!==this.type;z&&I.traverse(function(W){W.material&&(Array.isArray(W.material)?W.material.forEach(Y=>Y.needsUpdate=!0):W.material.needsUpdate=!0)});for(let W=0,Y=w.length;W<Y;W++){let k=w[W],H=k.shadow;if(H===void 0){Ce("WebGLShadowMap:",k,"has no shadow.");continue}if(H.autoUpdate===!1&&H.needsUpdate===!1)continue;s.copy(H.mapSize);let $=H.getFrameExtents();if(s.multiply($),r.copy(H.mapSize),(s.x>h||s.y>h)&&(s.x>h&&(r.x=Math.floor(h/$.x),s.x=r.x*$.x,H.mapSize.x=r.x),s.y>h&&(r.y=Math.floor(h/$.y),s.y=r.y*$.y,H.mapSize.y=r.y)),H.map===null||z===!0){if(H.map!==null&&(H.map.depthTexture!==null&&(H.map.depthTexture.dispose(),H.map.depthTexture=null),H.map.dispose()),this.type===Ti){if(k.isPointLight){Ce("WebGLShadowMap: VSM shadow maps are not supported for PointLights. Use PCF or BasicShadowMap instead.");continue}H.map=new Nt(s.x,s.y,{format:ei,type:on,minFilter:_t,magFilter:_t,generateMipmaps:!1}),H.map.texture.name=k.name+".shadowMap",H.map.depthTexture=new Ln(s.x,s.y,Kt),H.map.depthTexture.name=k.name+".shadowMapDepth",H.map.depthTexture.format=tn,H.map.depthTexture.compareFunction=null,H.map.depthTexture.minFilter=gt,H.map.depthTexture.magFilter=gt}else{k.isPointLight?(H.map=new Yi(s.x),H.map.depthTexture=new Ws(s.x,$t)):(H.map=new Nt(s.x,s.y),H.map.depthTexture=new Ln(s.x,s.y,$t)),H.map.depthTexture.name=k.name+".shadowMap",H.map.depthTexture.format=tn;let ae=i.state.buffers.depth.getReversed();this.type===es?(H.map.depthTexture.compareFunction=ae?jr:Qr,H.map.depthTexture.minFilter=_t,H.map.depthTexture.magFilter=_t):(H.map.depthTexture.compareFunction=null,H.map.depthTexture.minFilter=gt,H.map.depthTexture.magFilter=gt)}H.camera.updateProjectionMatrix()}let he=H.map.isWebGLCubeRenderTarget?6:1;for(let ae=0;ae<he;ae++){if(H.map.isWebGLCubeRenderTarget)i.setRenderTarget(H.map,ae),i.clear();else{ae===0&&(i.setRenderTarget(H.map),i.clear());let ue=H.getViewport(ae);a.set(r.x*ue.x,r.y*ue.y,r.x*ue.z,r.y*ue.w),V.viewport(a)}if(k.isPointLight){let ue=H.camera,Fe=H.matrix,De=k.distance||ue.far;De!==ue.far&&(ue.far=De,ue.updateProjectionMatrix()),cs.setFromMatrixPosition(k.matrixWorld),ue.position.copy(cs),_o.copy(ue.position),_o.add(Ap[ae]),ue.up.copy(Tp[ae]),ue.lookAt(_o),ue.updateMatrixWorld(),Fe.makeTranslation(-cs.x,-cs.y,-cs.z),ic.multiplyMatrices(ue.projectionMatrix,ue.matrixWorldInverse),H._frustum.setFromProjectionMatrix(ic,ue.coordinateSystem,ue.reversedDepth)}else H.updateMatrices(k);n=H.getFrustum(),A(I,B,H.camera,k,this.type)}H.isPointLightShadow!==!0&&this.type===Ti&&b(H,B),H.needsUpdate=!1}u=this.type,m.needsUpdate=!1,i.setRenderTarget(v,M,L)};function b(w,I){let B=e.update(y);p.defines.VSM_SAMPLES!==w.blurSamples&&(p.defines.VSM_SAMPLES=w.blurSamples,d.defines.VSM_SAMPLES=w.blurSamples,p.needsUpdate=!0,d.needsUpdate=!0),w.mapPass===null&&(w.mapPass=new Nt(s.x,s.y,{format:ei,type:on})),p.uniforms.shadow_pass.value=w.map.depthTexture,p.uniforms.resolution.value=w.mapSize,p.uniforms.radius.value=w.radius,i.setRenderTarget(w.mapPass),i.clear(),i.renderBufferDirect(I,null,B,p,y,null),d.uniforms.shadow_pass.value=w.mapPass.texture,d.uniforms.resolution.value=w.mapSize,d.uniforms.radius.value=w.radius,i.setRenderTarget(w.map),i.clear(),i.renderBufferDirect(I,null,B,d,y,null)}function T(w,I,B,v){let M=null,L=B.isPointLight===!0?w.customDistanceMaterial:w.customDepthMaterial;if(L!==void 0)M=L;else if(M=B.isPointLight===!0?c:o,i.localClippingEnabled&&I.clipShadows===!0&&Array.isArray(I.clippingPlanes)&&I.clippingPlanes.length!==0||I.displacementMap&&I.displacementScale!==0||I.alphaMap&&I.alphaTest>0||I.map&&I.alphaTest>0||I.alphaToCoverage===!0){let V=M.uuid,z=I.uuid,W=l[V];W===void 0&&(W={},l[V]=W);let Y=W[z];Y===void 0&&(Y=M.clone(),W[z]=Y,I.addEventListener("dispose",E)),M=Y}if(M.visible=I.visible,M.wireframe=I.wireframe,v===Ti?M.side=I.shadowSide!==null?I.shadowSide:I.side:M.side=I.shadowSide!==null?I.shadowSide:f[I.side],M.alphaMap=I.alphaMap,M.alphaTest=I.alphaToCoverage===!0?.5:I.alphaTest,M.map=I.map,M.clipShadows=I.clipShadows,M.clippingPlanes=I.clippingPlanes,M.clipIntersection=I.clipIntersection,M.displacementMap=I.displacementMap,M.displacementScale=I.displacementScale,M.displacementBias=I.displacementBias,M.wireframeLinewidth=I.wireframeLinewidth,M.linewidth=I.linewidth,B.isPointLight===!0&&M.isMeshDistanceMaterial===!0){let V=i.properties.get(M);V.light=B}return M}function A(w,I,B,v,M){if(w.visible===!1)return;if(w.layers.test(I.layers)&&(w.isMesh||w.isLine||w.isPoints)&&(w.castShadow||w.receiveShadow&&M===Ti)&&(!w.frustumCulled||n.intersectsObject(w))){w.modelViewMatrix.multiplyMatrices(B.matrixWorldInverse,w.matrixWorld);let z=e.update(w),W=w.material;if(Array.isArray(W)){let Y=z.groups;for(let k=0,H=Y.length;k<H;k++){let $=Y[k],he=W[$.materialIndex];if(he&&he.visible){let ae=T(w,he,v,M);w.onBeforeShadow(i,w,I,B,z,ae,$),i.renderBufferDirect(B,null,z,ae,w,$),w.onAfterShadow(i,w,I,B,z,ae,$)}}}else if(W.visible){let Y=T(w,W,v,M);w.onBeforeShadow(i,w,I,B,z,Y,null),i.renderBufferDirect(B,null,z,Y,w,null),w.onAfterShadow(i,w,I,B,z,Y,null)}}let V=w.children;for(let z=0,W=V.length;z<W;z++)A(V[z],I,B,v,M)}function E(w){w.target.removeEventListener("dispose",E);for(let B in l){let v=l[B],M=w.target.uuid;M in v&&(v[M].dispose(),delete v[M])}}}var wp={[sr]:rr,[ar]:cr,[or]:hr,[Yn]:lr,[rr]:sr,[cr]:ar,[hr]:or,[lr]:Yn};function Cp(i,e){function t(){let R=!1,ce=new ot,ee=null,de=new ot(0,0,0,0);return{setMask:function(Q){ee!==Q&&!R&&(i.colorMask(Q,Q,Q,Q),ee=Q)},setLocked:function(Q){R=Q},setClear:function(Q,Z,te,Re,et){et===!0&&(Q*=Re,Z*=Re,te*=Re),ce.set(Q,Z,te,Re),de.equals(ce)===!1&&(i.clearColor(Q,Z,te,Re),de.copy(ce))},reset:function(){R=!1,ee=null,de.set(-1,0,0,0)}}}function n(){let R=!1,ce=!1,ee=null,de=null,Q=null;return{setReversed:function(Z){if(ce!==Z){let te=e.get("EXT_clip_control");Z?te.clipControlEXT(te.LOWER_LEFT_EXT,te.ZERO_TO_ONE_EXT):te.clipControlEXT(te.LOWER_LEFT_EXT,te.NEGATIVE_ONE_TO_ONE_EXT),ce=Z;let Re=Q;Q=null,this.setClear(Re)}},getReversed:function(){return ce},setTest:function(Z){Z?K(i.DEPTH_TEST):pe(i.DEPTH_TEST)},setMask:function(Z){ee!==Z&&!R&&(i.depthMask(Z),ee=Z)},setFunc:function(Z){if(ce&&(Z=wp[Z]),de!==Z){switch(Z){case sr:i.depthFunc(i.NEVER);break;case rr:i.depthFunc(i.ALWAYS);break;case ar:i.depthFunc(i.LESS);break;case Yn:i.depthFunc(i.LEQUAL);break;case or:i.depthFunc(i.EQUAL);break;case lr:i.depthFunc(i.GEQUAL);break;case cr:i.depthFunc(i.GREATER);break;case hr:i.depthFunc(i.NOTEQUAL);break;default:i.depthFunc(i.LEQUAL)}de=Z}},setLocked:function(Z){R=Z},setClear:function(Z){Q!==Z&&(ce&&(Z=1-Z),i.clearDepth(Z),Q=Z)},reset:function(){R=!1,ee=null,de=null,Q=null,ce=!1}}}function s(){let R=!1,ce=null,ee=null,de=null,Q=null,Z=null,te=null,Re=null,et=null;return{setTest:function(Ye){R||(Ye?K(i.STENCIL_TEST):pe(i.STENCIL_TEST))},setMask:function(Ye){ce!==Ye&&!R&&(i.stencilMask(Ye),ce=Ye)},setFunc:function(Ye,Qt,hn){(ee!==Ye||de!==Qt||Q!==hn)&&(i.stencilFunc(Ye,Qt,hn),ee=Ye,de=Qt,Q=hn)},setOp:function(Ye,Qt,hn){(Z!==Ye||te!==Qt||Re!==hn)&&(i.stencilOp(Ye,Qt,hn),Z=Ye,te=Qt,Re=hn)},setLocked:function(Ye){R=Ye},setClear:function(Ye){et!==Ye&&(i.clearStencil(Ye),et=Ye)},reset:function(){R=!1,ce=null,ee=null,de=null,Q=null,Z=null,te=null,Re=null,et=null}}}let r=new t,a=new n,o=new s,c=new WeakMap,l=new WeakMap,h={},f={},p=new WeakMap,d=[],_=null,y=!1,m=null,u=null,b=null,T=null,A=null,E=null,w=null,I=new He(0,0,0),B=0,v=!1,M=null,L=null,V=null,z=null,W=null,Y=i.getParameter(i.MAX_COMBINED_TEXTURE_IMAGE_UNITS),k=!1,H=0,$=i.getParameter(i.VERSION);$.indexOf("WebGL")!==-1?(H=parseFloat(/^WebGL (\d)/.exec($)[1]),k=H>=1):$.indexOf("OpenGL ES")!==-1&&(H=parseFloat(/^OpenGL ES (\d)/.exec($)[1]),k=H>=2);let he=null,ae={},ue=i.getParameter(i.SCISSOR_BOX),Fe=i.getParameter(i.VIEWPORT),De=new ot().fromArray(ue),st=new ot().fromArray(Fe);function nt(R,ce,ee,de){let Q=new Uint8Array(4),Z=i.createTexture();i.bindTexture(R,Z),i.texParameteri(R,i.TEXTURE_MIN_FILTER,i.NEAREST),i.texParameteri(R,i.TEXTURE_MAG_FILTER,i.NEAREST);for(let te=0;te<ee;te++)R===i.TEXTURE_3D||R===i.TEXTURE_2D_ARRAY?i.texImage3D(ce,0,i.RGBA,1,1,de,0,i.RGBA,i.UNSIGNED_BYTE,Q):i.texImage2D(ce+te,0,i.RGBA,1,1,0,i.RGBA,i.UNSIGNED_BYTE,Q);return Z}let q={};q[i.TEXTURE_2D]=nt(i.TEXTURE_2D,i.TEXTURE_2D,1),q[i.TEXTURE_CUBE_MAP]=nt(i.TEXTURE_CUBE_MAP,i.TEXTURE_CUBE_MAP_POSITIVE_X,6),q[i.TEXTURE_2D_ARRAY]=nt(i.TEXTURE_2D_ARRAY,i.TEXTURE_2D_ARRAY,1,1),q[i.TEXTURE_3D]=nt(i.TEXTURE_3D,i.TEXTURE_3D,1,1),r.setClear(0,0,0,1),a.setClear(1),o.setClear(0),K(i.DEPTH_TEST),a.setFunc(Yn),Ue(!1),lt(Ba),K(i.CULL_FACE),qe(an);function K(R){h[R]!==!0&&(i.enable(R),h[R]=!0)}function pe(R){h[R]!==!1&&(i.disable(R),h[R]=!1)}function Pe(R,ce){return f[R]!==ce?(i.bindFramebuffer(R,ce),f[R]=ce,R===i.DRAW_FRAMEBUFFER&&(f[i.FRAMEBUFFER]=ce),R===i.FRAMEBUFFER&&(f[i.DRAW_FRAMEBUFFER]=ce),!0):!1}function _e(R,ce){let ee=d,de=!1;if(R){ee=p.get(ce),ee===void 0&&(ee=[],p.set(ce,ee));let Q=R.textures;if(ee.length!==Q.length||ee[0]!==i.COLOR_ATTACHMENT0){for(let Z=0,te=Q.length;Z<te;Z++)ee[Z]=i.COLOR_ATTACHMENT0+Z;ee.length=Q.length,de=!0}}else ee[0]!==i.BACK&&(ee[0]=i.BACK,de=!0);de&&i.drawBuffers(ee)}function ke(R){return _!==R?(i.useProgram(R),_=R,!0):!1}let pt={[In]:i.FUNC_ADD,[nl]:i.FUNC_SUBTRACT,[il]:i.FUNC_REVERSE_SUBTRACT};pt[sl]=i.MIN,pt[rl]=i.MAX;let Ve={[al]:i.ZERO,[ol]:i.ONE,[ll]:i.SRC_COLOR,[Ls]:i.SRC_ALPHA,[pl]:i.SRC_ALPHA_SATURATE,[dl]:i.DST_COLOR,[hl]:i.DST_ALPHA,[cl]:i.ONE_MINUS_SRC_COLOR,[Ds]:i.ONE_MINUS_SRC_ALPHA,[fl]:i.ONE_MINUS_DST_COLOR,[ul]:i.ONE_MINUS_DST_ALPHA,[ml]:i.CONSTANT_COLOR,[gl]:i.ONE_MINUS_CONSTANT_COLOR,[_l]:i.CONSTANT_ALPHA,[xl]:i.ONE_MINUS_CONSTANT_ALPHA};function qe(R,ce,ee,de,Q,Z,te,Re,et,Ye){if(R===an){y===!0&&(pe(i.BLEND),y=!1);return}if(y===!1&&(K(i.BLEND),y=!0),R!==tl){if(R!==m||Ye!==v){if((u!==In||A!==In)&&(i.blendEquation(i.FUNC_ADD),u=In,A=In),Ye)switch(R){case qn:i.blendFuncSeparate(i.ONE,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case za:i.blendFunc(i.ONE,i.ONE);break;case Va:i.blendFuncSeparate(i.ZERO,i.ONE_MINUS_SRC_COLOR,i.ZERO,i.ONE);break;case ka:i.blendFuncSeparate(i.DST_COLOR,i.ONE_MINUS_SRC_ALPHA,i.ZERO,i.ONE);break;default:Ee("WebGLState: Invalid blending: ",R);break}else switch(R){case qn:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case za:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE,i.ONE,i.ONE);break;case Va:Ee("WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case ka:Ee("WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:Ee("WebGLState: Invalid blending: ",R);break}b=null,T=null,E=null,w=null,I.set(0,0,0),B=0,m=R,v=Ye}return}Q=Q||ce,Z=Z||ee,te=te||de,(ce!==u||Q!==A)&&(i.blendEquationSeparate(pt[ce],pt[Q]),u=ce,A=Q),(ee!==b||de!==T||Z!==E||te!==w)&&(i.blendFuncSeparate(Ve[ee],Ve[de],Ve[Z],Ve[te]),b=ee,T=de,E=Z,w=te),(Re.equals(I)===!1||et!==B)&&(i.blendColor(Re.r,Re.g,Re.b,et),I.copy(Re),B=et),m=R,v=!1}function Ke(R,ce){R.side===rn?pe(i.CULL_FACE):K(i.CULL_FACE);let ee=R.side===Tt;ce&&(ee=!ee),Ue(ee),R.blending===qn&&R.transparent===!1?qe(an):qe(R.blending,R.blendEquation,R.blendSrc,R.blendDst,R.blendEquationAlpha,R.blendSrcAlpha,R.blendDstAlpha,R.blendColor,R.blendAlpha,R.premultipliedAlpha),a.setFunc(R.depthFunc),a.setTest(R.depthTest),a.setMask(R.depthWrite),r.setMask(R.colorWrite);let de=R.stencilWrite;o.setTest(de),de&&(o.setMask(R.stencilWriteMask),o.setFunc(R.stencilFunc,R.stencilRef,R.stencilFuncMask),o.setOp(R.stencilFail,R.stencilZFail,R.stencilZPass)),ct(R.polygonOffset,R.polygonOffsetFactor,R.polygonOffsetUnits),R.alphaToCoverage===!0?K(i.SAMPLE_ALPHA_TO_COVERAGE):pe(i.SAMPLE_ALPHA_TO_COVERAGE)}function Ue(R){M!==R&&(R?i.frontFace(i.CW):i.frontFace(i.CCW),M=R)}function lt(R){R!==Qo?(K(i.CULL_FACE),R!==L&&(R===Ba?i.cullFace(i.BACK):R===jo?i.cullFace(i.FRONT):i.cullFace(i.FRONT_AND_BACK))):pe(i.CULL_FACE),L=R}function C(R){R!==V&&(k&&i.lineWidth(R),V=R)}function ct(R,ce,ee){R?(K(i.POLYGON_OFFSET_FILL),(z!==ce||W!==ee)&&(i.polygonOffset(ce,ee),z=ce,W=ee)):pe(i.POLYGON_OFFSET_FILL)}function We(R){R?K(i.SCISSOR_TEST):pe(i.SCISSOR_TEST)}function je(R){R===void 0&&(R=i.TEXTURE0+Y-1),he!==R&&(i.activeTexture(R),he=R)}function ve(R,ce,ee){ee===void 0&&(he===null?ee=i.TEXTURE0+Y-1:ee=he);let de=ae[ee];de===void 0&&(de={type:void 0,texture:void 0},ae[ee]=de),(de.type!==R||de.texture!==ce)&&(he!==ee&&(i.activeTexture(ee),he=ee),i.bindTexture(R,ce||q[R]),de.type=R,de.texture=ce)}function S(){let R=ae[he];R!==void 0&&R.type!==void 0&&(i.bindTexture(R.type,null),R.type=void 0,R.texture=void 0)}function g(){try{i.compressedTexImage2D(...arguments)}catch(R){Ee("WebGLState:",R)}}function P(){try{i.compressedTexImage3D(...arguments)}catch(R){Ee("WebGLState:",R)}}function X(){try{i.texSubImage2D(...arguments)}catch(R){Ee("WebGLState:",R)}}function J(){try{i.texSubImage3D(...arguments)}catch(R){Ee("WebGLState:",R)}}function G(){try{i.compressedTexSubImage2D(...arguments)}catch(R){Ee("WebGLState:",R)}}function Me(){try{i.compressedTexSubImage3D(...arguments)}catch(R){Ee("WebGLState:",R)}}function ne(){try{i.texStorage2D(...arguments)}catch(R){Ee("WebGLState:",R)}}function xe(){try{i.texStorage3D(...arguments)}catch(R){Ee("WebGLState:",R)}}function we(){try{i.texImage2D(...arguments)}catch(R){Ee("WebGLState:",R)}}function j(){try{i.texImage3D(...arguments)}catch(R){Ee("WebGLState:",R)}}function se(R){De.equals(R)===!1&&(i.scissor(R.x,R.y,R.z,R.w),De.copy(R))}function ge(R){st.equals(R)===!1&&(i.viewport(R.x,R.y,R.z,R.w),st.copy(R))}function ye(R,ce){let ee=l.get(ce);ee===void 0&&(ee=new WeakMap,l.set(ce,ee));let de=ee.get(R);de===void 0&&(de=i.getUniformBlockIndex(ce,R.name),ee.set(R,de))}function ie(R,ce){let de=l.get(ce).get(R);c.get(ce)!==de&&(i.uniformBlockBinding(ce,de,R.__bindingPointIndex),c.set(ce,de))}function Ne(){i.disable(i.BLEND),i.disable(i.CULL_FACE),i.disable(i.DEPTH_TEST),i.disable(i.POLYGON_OFFSET_FILL),i.disable(i.SCISSOR_TEST),i.disable(i.STENCIL_TEST),i.disable(i.SAMPLE_ALPHA_TO_COVERAGE),i.blendEquation(i.FUNC_ADD),i.blendFunc(i.ONE,i.ZERO),i.blendFuncSeparate(i.ONE,i.ZERO,i.ONE,i.ZERO),i.blendColor(0,0,0,0),i.colorMask(!0,!0,!0,!0),i.clearColor(0,0,0,0),i.depthMask(!0),i.depthFunc(i.LESS),a.setReversed(!1),i.clearDepth(1),i.stencilMask(4294967295),i.stencilFunc(i.ALWAYS,0,4294967295),i.stencilOp(i.KEEP,i.KEEP,i.KEEP),i.clearStencil(0),i.cullFace(i.BACK),i.frontFace(i.CCW),i.polygonOffset(0,0),i.activeTexture(i.TEXTURE0),i.bindFramebuffer(i.FRAMEBUFFER,null),i.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),i.bindFramebuffer(i.READ_FRAMEBUFFER,null),i.useProgram(null),i.lineWidth(1),i.scissor(0,0,i.canvas.width,i.canvas.height),i.viewport(0,0,i.canvas.width,i.canvas.height),h={},he=null,ae={},f={},p=new WeakMap,d=[],_=null,y=!1,m=null,u=null,b=null,T=null,A=null,E=null,w=null,I=new He(0,0,0),B=0,v=!1,M=null,L=null,V=null,z=null,W=null,De.set(0,0,i.canvas.width,i.canvas.height),st.set(0,0,i.canvas.width,i.canvas.height),r.reset(),a.reset(),o.reset()}return{buffers:{color:r,depth:a,stencil:o},enable:K,disable:pe,bindFramebuffer:Pe,drawBuffers:_e,useProgram:ke,setBlending:qe,setMaterial:Ke,setFlipSided:Ue,setCullFace:lt,setLineWidth:C,setPolygonOffset:ct,setScissorTest:We,activeTexture:je,bindTexture:ve,unbindTexture:S,compressedTexImage2D:g,compressedTexImage3D:P,texImage2D:we,texImage3D:j,updateUBOMapping:ye,uniformBlockBinding:ie,texStorage2D:ne,texStorage3D:xe,texSubImage2D:X,texSubImage3D:J,compressedTexSubImage2D:G,compressedTexSubImage3D:Me,scissor:se,viewport:ge,reset:Ne}}function Rp(i,e,t,n,s,r,a){let o=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,c=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),l=new Je,h=new WeakMap,f,p=new WeakMap,d=!1;try{d=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function _(S,g){return d?new OffscreenCanvas(S,g):Vi("canvas")}function y(S,g,P){let X=1,J=ve(S);if((J.width>P||J.height>P)&&(X=P/Math.max(J.width,J.height)),X<1)if(typeof HTMLImageElement<"u"&&S instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&S instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&S instanceof ImageBitmap||typeof VideoFrame<"u"&&S instanceof VideoFrame){let G=Math.floor(X*J.width),Me=Math.floor(X*J.height);f===void 0&&(f=_(G,Me));let ne=g?_(G,Me):f;return ne.width=G,ne.height=Me,ne.getContext("2d").drawImage(S,0,0,G,Me),Ce("WebGLRenderer: Texture has been resized from ("+J.width+"x"+J.height+") to ("+G+"x"+Me+")."),ne}else return"data"in S&&Ce("WebGLRenderer: Image in DataTexture is too big ("+J.width+"x"+J.height+")."),S;return S}function m(S){return S.generateMipmaps}function u(S){i.generateMipmap(S)}function b(S){return S.isWebGLCubeRenderTarget?i.TEXTURE_CUBE_MAP:S.isWebGL3DRenderTarget?i.TEXTURE_3D:S.isWebGLArrayRenderTarget||S.isCompressedArrayTexture?i.TEXTURE_2D_ARRAY:i.TEXTURE_2D}function T(S,g,P,X,J=!1){if(S!==null){if(i[S]!==void 0)return i[S];Ce("WebGLRenderer: Attempt to use non-existing WebGL internal format '"+S+"'")}let G=g;if(g===i.RED&&(P===i.FLOAT&&(G=i.R32F),P===i.HALF_FLOAT&&(G=i.R16F),P===i.UNSIGNED_BYTE&&(G=i.R8)),g===i.RED_INTEGER&&(P===i.UNSIGNED_BYTE&&(G=i.R8UI),P===i.UNSIGNED_SHORT&&(G=i.R16UI),P===i.UNSIGNED_INT&&(G=i.R32UI),P===i.BYTE&&(G=i.R8I),P===i.SHORT&&(G=i.R16I),P===i.INT&&(G=i.R32I)),g===i.RG&&(P===i.FLOAT&&(G=i.RG32F),P===i.HALF_FLOAT&&(G=i.RG16F),P===i.UNSIGNED_BYTE&&(G=i.RG8)),g===i.RG_INTEGER&&(P===i.UNSIGNED_BYTE&&(G=i.RG8UI),P===i.UNSIGNED_SHORT&&(G=i.RG16UI),P===i.UNSIGNED_INT&&(G=i.RG32UI),P===i.BYTE&&(G=i.RG8I),P===i.SHORT&&(G=i.RG16I),P===i.INT&&(G=i.RG32I)),g===i.RGB_INTEGER&&(P===i.UNSIGNED_BYTE&&(G=i.RGB8UI),P===i.UNSIGNED_SHORT&&(G=i.RGB16UI),P===i.UNSIGNED_INT&&(G=i.RGB32UI),P===i.BYTE&&(G=i.RGB8I),P===i.SHORT&&(G=i.RGB16I),P===i.INT&&(G=i.RGB32I)),g===i.RGBA_INTEGER&&(P===i.UNSIGNED_BYTE&&(G=i.RGBA8UI),P===i.UNSIGNED_SHORT&&(G=i.RGBA16UI),P===i.UNSIGNED_INT&&(G=i.RGBA32UI),P===i.BYTE&&(G=i.RGBA8I),P===i.SHORT&&(G=i.RGBA16I),P===i.INT&&(G=i.RGBA32I)),g===i.RGB&&(P===i.UNSIGNED_INT_5_9_9_9_REV&&(G=i.RGB9_E5),P===i.UNSIGNED_INT_10F_11F_11F_REV&&(G=i.R11F_G11F_B10F)),g===i.RGBA){let Me=J?Bi:ze.getTransfer(X);P===i.FLOAT&&(G=i.RGBA32F),P===i.HALF_FLOAT&&(G=i.RGBA16F),P===i.UNSIGNED_BYTE&&(G=Me===Xe?i.SRGB8_ALPHA8:i.RGBA8),P===i.UNSIGNED_SHORT_4_4_4_4&&(G=i.RGBA4),P===i.UNSIGNED_SHORT_5_5_5_1&&(G=i.RGB5_A1)}return(G===i.R16F||G===i.R32F||G===i.RG16F||G===i.RG32F||G===i.RGBA16F||G===i.RGBA32F)&&e.get("EXT_color_buffer_float"),G}function A(S,g){let P;return S?g===null||g===$t||g===wi?P=i.DEPTH24_STENCIL8:g===Kt?P=i.DEPTH32F_STENCIL8:g===Ei&&(P=i.DEPTH24_STENCIL8,Ce("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):g===null||g===$t||g===wi?P=i.DEPTH_COMPONENT24:g===Kt?P=i.DEPTH_COMPONENT32F:g===Ei&&(P=i.DEPTH_COMPONENT16),P}function E(S,g){return m(S)===!0||S.isFramebufferTexture&&S.minFilter!==gt&&S.minFilter!==_t?Math.log2(Math.max(g.width,g.height))+1:S.mipmaps!==void 0&&S.mipmaps.length>0?S.mipmaps.length:S.isCompressedTexture&&Array.isArray(S.image)?g.mipmaps.length:1}function w(S){let g=S.target;g.removeEventListener("dispose",w),B(g),g.isVideoTexture&&h.delete(g)}function I(S){let g=S.target;g.removeEventListener("dispose",I),M(g)}function B(S){let g=n.get(S);if(g.__webglInit===void 0)return;let P=S.source,X=p.get(P);if(X){let J=X[g.__cacheKey];J.usedTimes--,J.usedTimes===0&&v(S),Object.keys(X).length===0&&p.delete(P)}n.remove(S)}function v(S){let g=n.get(S);i.deleteTexture(g.__webglTexture);let P=S.source,X=p.get(P);delete X[g.__cacheKey],a.memory.textures--}function M(S){let g=n.get(S);if(S.depthTexture&&(S.depthTexture.dispose(),n.remove(S.depthTexture)),S.isWebGLCubeRenderTarget)for(let X=0;X<6;X++){if(Array.isArray(g.__webglFramebuffer[X]))for(let J=0;J<g.__webglFramebuffer[X].length;J++)i.deleteFramebuffer(g.__webglFramebuffer[X][J]);else i.deleteFramebuffer(g.__webglFramebuffer[X]);g.__webglDepthbuffer&&i.deleteRenderbuffer(g.__webglDepthbuffer[X])}else{if(Array.isArray(g.__webglFramebuffer))for(let X=0;X<g.__webglFramebuffer.length;X++)i.deleteFramebuffer(g.__webglFramebuffer[X]);else i.deleteFramebuffer(g.__webglFramebuffer);if(g.__webglDepthbuffer&&i.deleteRenderbuffer(g.__webglDepthbuffer),g.__webglMultisampledFramebuffer&&i.deleteFramebuffer(g.__webglMultisampledFramebuffer),g.__webglColorRenderbuffer)for(let X=0;X<g.__webglColorRenderbuffer.length;X++)g.__webglColorRenderbuffer[X]&&i.deleteRenderbuffer(g.__webglColorRenderbuffer[X]);g.__webglDepthRenderbuffer&&i.deleteRenderbuffer(g.__webglDepthRenderbuffer)}let P=S.textures;for(let X=0,J=P.length;X<J;X++){let G=n.get(P[X]);G.__webglTexture&&(i.deleteTexture(G.__webglTexture),a.memory.textures--),n.remove(P[X])}n.remove(S)}let L=0;function V(){L=0}function z(){let S=L;return S>=s.maxTextures&&Ce("WebGLTextures: Trying to use "+S+" texture units while this GPU supports only "+s.maxTextures),L+=1,S}function W(S){let g=[];return g.push(S.wrapS),g.push(S.wrapT),g.push(S.wrapR||0),g.push(S.magFilter),g.push(S.minFilter),g.push(S.anisotropy),g.push(S.internalFormat),g.push(S.format),g.push(S.type),g.push(S.generateMipmaps),g.push(S.premultiplyAlpha),g.push(S.flipY),g.push(S.unpackAlignment),g.push(S.colorSpace),g.join()}function Y(S,g){let P=n.get(S);if(S.isVideoTexture&&We(S),S.isRenderTargetTexture===!1&&S.isExternalTexture!==!0&&S.version>0&&P.__version!==S.version){let X=S.image;if(X===null)Ce("WebGLRenderer: Texture marked for update but no image data found.");else if(X.complete===!1)Ce("WebGLRenderer: Texture marked for update but image is incomplete");else{q(P,S,g);return}}else S.isExternalTexture&&(P.__webglTexture=S.sourceTexture?S.sourceTexture:null);t.bindTexture(i.TEXTURE_2D,P.__webglTexture,i.TEXTURE0+g)}function k(S,g){let P=n.get(S);if(S.isRenderTargetTexture===!1&&S.version>0&&P.__version!==S.version){q(P,S,g);return}else S.isExternalTexture&&(P.__webglTexture=S.sourceTexture?S.sourceTexture:null);t.bindTexture(i.TEXTURE_2D_ARRAY,P.__webglTexture,i.TEXTURE0+g)}function H(S,g){let P=n.get(S);if(S.isRenderTargetTexture===!1&&S.version>0&&P.__version!==S.version){q(P,S,g);return}t.bindTexture(i.TEXTURE_3D,P.__webglTexture,i.TEXTURE0+g)}function $(S,g){let P=n.get(S);if(S.isCubeDepthTexture!==!0&&S.version>0&&P.__version!==S.version){K(P,S,g);return}t.bindTexture(i.TEXTURE_CUBE_MAP,P.__webglTexture,i.TEXTURE0+g)}let he={[Us]:i.REPEAT,[en]:i.CLAMP_TO_EDGE,[Ns]:i.MIRRORED_REPEAT},ae={[gt]:i.NEAREST,[Ml]:i.NEAREST_MIPMAP_NEAREST,[ns]:i.NEAREST_MIPMAP_LINEAR,[_t]:i.LINEAR,[fr]:i.LINEAR_MIPMAP_NEAREST,[Fn]:i.LINEAR_MIPMAP_LINEAR},ue={[Tl]:i.NEVER,[Il]:i.ALWAYS,[El]:i.LESS,[Qr]:i.LEQUAL,[wl]:i.EQUAL,[jr]:i.GEQUAL,[Cl]:i.GREATER,[Rl]:i.NOTEQUAL};function Fe(S,g){if(g.type===Kt&&e.has("OES_texture_float_linear")===!1&&(g.magFilter===_t||g.magFilter===fr||g.magFilter===ns||g.magFilter===Fn||g.minFilter===_t||g.minFilter===fr||g.minFilter===ns||g.minFilter===Fn)&&Ce("WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),i.texParameteri(S,i.TEXTURE_WRAP_S,he[g.wrapS]),i.texParameteri(S,i.TEXTURE_WRAP_T,he[g.wrapT]),(S===i.TEXTURE_3D||S===i.TEXTURE_2D_ARRAY)&&i.texParameteri(S,i.TEXTURE_WRAP_R,he[g.wrapR]),i.texParameteri(S,i.TEXTURE_MAG_FILTER,ae[g.magFilter]),i.texParameteri(S,i.TEXTURE_MIN_FILTER,ae[g.minFilter]),g.compareFunction&&(i.texParameteri(S,i.TEXTURE_COMPARE_MODE,i.COMPARE_REF_TO_TEXTURE),i.texParameteri(S,i.TEXTURE_COMPARE_FUNC,ue[g.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(g.magFilter===gt||g.minFilter!==ns&&g.minFilter!==Fn||g.type===Kt&&e.has("OES_texture_float_linear")===!1)return;if(g.anisotropy>1||n.get(g).__currentAnisotropy){let P=e.get("EXT_texture_filter_anisotropic");i.texParameterf(S,P.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(g.anisotropy,s.getMaxAnisotropy())),n.get(g).__currentAnisotropy=g.anisotropy}}}function De(S,g){let P=!1;S.__webglInit===void 0&&(S.__webglInit=!0,g.addEventListener("dispose",w));let X=g.source,J=p.get(X);J===void 0&&(J={},p.set(X,J));let G=W(g);if(G!==S.__cacheKey){J[G]===void 0&&(J[G]={texture:i.createTexture(),usedTimes:0},a.memory.textures++,P=!0),J[G].usedTimes++;let Me=J[S.__cacheKey];Me!==void 0&&(J[S.__cacheKey].usedTimes--,Me.usedTimes===0&&v(g)),S.__cacheKey=G,S.__webglTexture=J[G].texture}return P}function st(S,g,P){return Math.floor(Math.floor(S/P)/g)}function nt(S,g,P,X){let G=S.updateRanges;if(G.length===0)t.texSubImage2D(i.TEXTURE_2D,0,0,0,g.width,g.height,P,X,g.data);else{G.sort((j,se)=>j.start-se.start);let Me=0;for(let j=1;j<G.length;j++){let se=G[Me],ge=G[j],ye=se.start+se.count,ie=st(ge.start,g.width,4),Ne=st(se.start,g.width,4);ge.start<=ye+1&&ie===Ne&&st(ge.start+ge.count-1,g.width,4)===ie?se.count=Math.max(se.count,ge.start+ge.count-se.start):(++Me,G[Me]=ge)}G.length=Me+1;let ne=i.getParameter(i.UNPACK_ROW_LENGTH),xe=i.getParameter(i.UNPACK_SKIP_PIXELS),we=i.getParameter(i.UNPACK_SKIP_ROWS);i.pixelStorei(i.UNPACK_ROW_LENGTH,g.width);for(let j=0,se=G.length;j<se;j++){let ge=G[j],ye=Math.floor(ge.start/4),ie=Math.ceil(ge.count/4),Ne=ye%g.width,R=Math.floor(ye/g.width),ce=ie,ee=1;i.pixelStorei(i.UNPACK_SKIP_PIXELS,Ne),i.pixelStorei(i.UNPACK_SKIP_ROWS,R),t.texSubImage2D(i.TEXTURE_2D,0,Ne,R,ce,ee,P,X,g.data)}S.clearUpdateRanges(),i.pixelStorei(i.UNPACK_ROW_LENGTH,ne),i.pixelStorei(i.UNPACK_SKIP_PIXELS,xe),i.pixelStorei(i.UNPACK_SKIP_ROWS,we)}}function q(S,g,P){let X=i.TEXTURE_2D;(g.isDataArrayTexture||g.isCompressedArrayTexture)&&(X=i.TEXTURE_2D_ARRAY),g.isData3DTexture&&(X=i.TEXTURE_3D);let J=De(S,g),G=g.source;t.bindTexture(X,S.__webglTexture,i.TEXTURE0+P);let Me=n.get(G);if(G.version!==Me.__version||J===!0){t.activeTexture(i.TEXTURE0+P);let ne=ze.getPrimaries(ze.workingColorSpace),xe=g.colorSpace===Mn?null:ze.getPrimaries(g.colorSpace),we=g.colorSpace===Mn||ne===xe?i.NONE:i.BROWSER_DEFAULT_WEBGL;i.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,g.flipY),i.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,g.premultiplyAlpha),i.pixelStorei(i.UNPACK_ALIGNMENT,g.unpackAlignment),i.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,we);let j=y(g.image,!1,s.maxTextureSize);j=je(g,j);let se=r.convert(g.format,g.colorSpace),ge=r.convert(g.type),ye=T(g.internalFormat,se,ge,g.colorSpace,g.isVideoTexture);Fe(X,g);let ie,Ne=g.mipmaps,R=g.isVideoTexture!==!0,ce=Me.__version===void 0||J===!0,ee=G.dataReady,de=E(g,j);if(g.isDepthTexture)ye=A(g.format===On,g.type),ce&&(R?t.texStorage2D(i.TEXTURE_2D,1,ye,j.width,j.height):t.texImage2D(i.TEXTURE_2D,0,ye,j.width,j.height,0,se,ge,null));else if(g.isDataTexture)if(Ne.length>0){R&&ce&&t.texStorage2D(i.TEXTURE_2D,de,ye,Ne[0].width,Ne[0].height);for(let Q=0,Z=Ne.length;Q<Z;Q++)ie=Ne[Q],R?ee&&t.texSubImage2D(i.TEXTURE_2D,Q,0,0,ie.width,ie.height,se,ge,ie.data):t.texImage2D(i.TEXTURE_2D,Q,ye,ie.width,ie.height,0,se,ge,ie.data);g.generateMipmaps=!1}else R?(ce&&t.texStorage2D(i.TEXTURE_2D,de,ye,j.width,j.height),ee&&nt(g,j,se,ge)):t.texImage2D(i.TEXTURE_2D,0,ye,j.width,j.height,0,se,ge,j.data);else if(g.isCompressedTexture)if(g.isCompressedArrayTexture){R&&ce&&t.texStorage3D(i.TEXTURE_2D_ARRAY,de,ye,Ne[0].width,Ne[0].height,j.depth);for(let Q=0,Z=Ne.length;Q<Z;Q++)if(ie=Ne[Q],g.format!==Ht)if(se!==null)if(R){if(ee)if(g.layerUpdates.size>0){let te=ho(ie.width,ie.height,g.format,g.type);for(let Re of g.layerUpdates){let et=ie.data.subarray(Re*te/ie.data.BYTES_PER_ELEMENT,(Re+1)*te/ie.data.BYTES_PER_ELEMENT);t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,Q,0,0,Re,ie.width,ie.height,1,se,et)}g.clearLayerUpdates()}else t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,Q,0,0,0,ie.width,ie.height,j.depth,se,ie.data)}else t.compressedTexImage3D(i.TEXTURE_2D_ARRAY,Q,ye,ie.width,ie.height,j.depth,0,ie.data,0,0);else Ce("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else R?ee&&t.texSubImage3D(i.TEXTURE_2D_ARRAY,Q,0,0,0,ie.width,ie.height,j.depth,se,ge,ie.data):t.texImage3D(i.TEXTURE_2D_ARRAY,Q,ye,ie.width,ie.height,j.depth,0,se,ge,ie.data)}else{R&&ce&&t.texStorage2D(i.TEXTURE_2D,de,ye,Ne[0].width,Ne[0].height);for(let Q=0,Z=Ne.length;Q<Z;Q++)ie=Ne[Q],g.format!==Ht?se!==null?R?ee&&t.compressedTexSubImage2D(i.TEXTURE_2D,Q,0,0,ie.width,ie.height,se,ie.data):t.compressedTexImage2D(i.TEXTURE_2D,Q,ye,ie.width,ie.height,0,ie.data):Ce("WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):R?ee&&t.texSubImage2D(i.TEXTURE_2D,Q,0,0,ie.width,ie.height,se,ge,ie.data):t.texImage2D(i.TEXTURE_2D,Q,ye,ie.width,ie.height,0,se,ge,ie.data)}else if(g.isDataArrayTexture)if(R){if(ce&&t.texStorage3D(i.TEXTURE_2D_ARRAY,de,ye,j.width,j.height,j.depth),ee)if(g.layerUpdates.size>0){let Q=ho(j.width,j.height,g.format,g.type);for(let Z of g.layerUpdates){let te=j.data.subarray(Z*Q/j.data.BYTES_PER_ELEMENT,(Z+1)*Q/j.data.BYTES_PER_ELEMENT);t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,Z,j.width,j.height,1,se,ge,te)}g.clearLayerUpdates()}else t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,0,j.width,j.height,j.depth,se,ge,j.data)}else t.texImage3D(i.TEXTURE_2D_ARRAY,0,ye,j.width,j.height,j.depth,0,se,ge,j.data);else if(g.isData3DTexture)R?(ce&&t.texStorage3D(i.TEXTURE_3D,de,ye,j.width,j.height,j.depth),ee&&t.texSubImage3D(i.TEXTURE_3D,0,0,0,0,j.width,j.height,j.depth,se,ge,j.data)):t.texImage3D(i.TEXTURE_3D,0,ye,j.width,j.height,j.depth,0,se,ge,j.data);else if(g.isFramebufferTexture){if(ce)if(R)t.texStorage2D(i.TEXTURE_2D,de,ye,j.width,j.height);else{let Q=j.width,Z=j.height;for(let te=0;te<de;te++)t.texImage2D(i.TEXTURE_2D,te,ye,Q,Z,0,se,ge,null),Q>>=1,Z>>=1}}else if(Ne.length>0){if(R&&ce){let Q=ve(Ne[0]);t.texStorage2D(i.TEXTURE_2D,de,ye,Q.width,Q.height)}for(let Q=0,Z=Ne.length;Q<Z;Q++)ie=Ne[Q],R?ee&&t.texSubImage2D(i.TEXTURE_2D,Q,0,0,se,ge,ie):t.texImage2D(i.TEXTURE_2D,Q,ye,se,ge,ie);g.generateMipmaps=!1}else if(R){if(ce){let Q=ve(j);t.texStorage2D(i.TEXTURE_2D,de,ye,Q.width,Q.height)}ee&&t.texSubImage2D(i.TEXTURE_2D,0,0,0,se,ge,j)}else t.texImage2D(i.TEXTURE_2D,0,ye,se,ge,j);m(g)&&u(X),Me.__version=G.version,g.onUpdate&&g.onUpdate(g)}S.__version=g.version}function K(S,g,P){if(g.image.length!==6)return;let X=De(S,g),J=g.source;t.bindTexture(i.TEXTURE_CUBE_MAP,S.__webglTexture,i.TEXTURE0+P);let G=n.get(J);if(J.version!==G.__version||X===!0){t.activeTexture(i.TEXTURE0+P);let Me=ze.getPrimaries(ze.workingColorSpace),ne=g.colorSpace===Mn?null:ze.getPrimaries(g.colorSpace),xe=g.colorSpace===Mn||Me===ne?i.NONE:i.BROWSER_DEFAULT_WEBGL;i.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,g.flipY),i.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,g.premultiplyAlpha),i.pixelStorei(i.UNPACK_ALIGNMENT,g.unpackAlignment),i.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,xe);let we=g.isCompressedTexture||g.image[0].isCompressedTexture,j=g.image[0]&&g.image[0].isDataTexture,se=[];for(let Z=0;Z<6;Z++)!we&&!j?se[Z]=y(g.image[Z],!0,s.maxCubemapSize):se[Z]=j?g.image[Z].image:g.image[Z],se[Z]=je(g,se[Z]);let ge=se[0],ye=r.convert(g.format,g.colorSpace),ie=r.convert(g.type),Ne=T(g.internalFormat,ye,ie,g.colorSpace),R=g.isVideoTexture!==!0,ce=G.__version===void 0||X===!0,ee=J.dataReady,de=E(g,ge);Fe(i.TEXTURE_CUBE_MAP,g);let Q;if(we){R&&ce&&t.texStorage2D(i.TEXTURE_CUBE_MAP,de,Ne,ge.width,ge.height);for(let Z=0;Z<6;Z++){Q=se[Z].mipmaps;for(let te=0;te<Q.length;te++){let Re=Q[te];g.format!==Ht?ye!==null?R?ee&&t.compressedTexSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,te,0,0,Re.width,Re.height,ye,Re.data):t.compressedTexImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,te,Ne,Re.width,Re.height,0,Re.data):Ce("WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):R?ee&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,te,0,0,Re.width,Re.height,ye,ie,Re.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,te,Ne,Re.width,Re.height,0,ye,ie,Re.data)}}}else{if(Q=g.mipmaps,R&&ce){Q.length>0&&de++;let Z=ve(se[0]);t.texStorage2D(i.TEXTURE_CUBE_MAP,de,Ne,Z.width,Z.height)}for(let Z=0;Z<6;Z++)if(j){R?ee&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,0,0,0,se[Z].width,se[Z].height,ye,ie,se[Z].data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,0,Ne,se[Z].width,se[Z].height,0,ye,ie,se[Z].data);for(let te=0;te<Q.length;te++){let et=Q[te].image[Z].image;R?ee&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,te+1,0,0,et.width,et.height,ye,ie,et.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,te+1,Ne,et.width,et.height,0,ye,ie,et.data)}}else{R?ee&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,0,0,0,ye,ie,se[Z]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,0,Ne,ye,ie,se[Z]);for(let te=0;te<Q.length;te++){let Re=Q[te];R?ee&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,te+1,0,0,ye,ie,Re.image[Z]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,te+1,Ne,ye,ie,Re.image[Z])}}}m(g)&&u(i.TEXTURE_CUBE_MAP),G.__version=J.version,g.onUpdate&&g.onUpdate(g)}S.__version=g.version}function pe(S,g,P,X,J,G){let Me=r.convert(P.format,P.colorSpace),ne=r.convert(P.type),xe=T(P.internalFormat,Me,ne,P.colorSpace),we=n.get(g),j=n.get(P);if(j.__renderTarget=g,!we.__hasExternalTextures){let se=Math.max(1,g.width>>G),ge=Math.max(1,g.height>>G);J===i.TEXTURE_3D||J===i.TEXTURE_2D_ARRAY?t.texImage3D(J,G,xe,se,ge,g.depth,0,Me,ne,null):t.texImage2D(J,G,xe,se,ge,0,Me,ne,null)}t.bindFramebuffer(i.FRAMEBUFFER,S),ct(g)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,X,J,j.__webglTexture,0,C(g)):(J===i.TEXTURE_2D||J>=i.TEXTURE_CUBE_MAP_POSITIVE_X&&J<=i.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&i.framebufferTexture2D(i.FRAMEBUFFER,X,J,j.__webglTexture,G),t.bindFramebuffer(i.FRAMEBUFFER,null)}function Pe(S,g,P){if(i.bindRenderbuffer(i.RENDERBUFFER,S),g.depthBuffer){let X=g.depthTexture,J=X&&X.isDepthTexture?X.type:null,G=A(g.stencilBuffer,J),Me=g.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;ct(g)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,C(g),G,g.width,g.height):P?i.renderbufferStorageMultisample(i.RENDERBUFFER,C(g),G,g.width,g.height):i.renderbufferStorage(i.RENDERBUFFER,G,g.width,g.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,Me,i.RENDERBUFFER,S)}else{let X=g.textures;for(let J=0;J<X.length;J++){let G=X[J],Me=r.convert(G.format,G.colorSpace),ne=r.convert(G.type),xe=T(G.internalFormat,Me,ne,G.colorSpace);ct(g)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,C(g),xe,g.width,g.height):P?i.renderbufferStorageMultisample(i.RENDERBUFFER,C(g),xe,g.width,g.height):i.renderbufferStorage(i.RENDERBUFFER,xe,g.width,g.height)}}i.bindRenderbuffer(i.RENDERBUFFER,null)}function _e(S,g,P){let X=g.isWebGLCubeRenderTarget===!0;if(t.bindFramebuffer(i.FRAMEBUFFER,S),!(g.depthTexture&&g.depthTexture.isDepthTexture))throw new Error("renderTarget.depthTexture must be an instance of THREE.DepthTexture");let J=n.get(g.depthTexture);if(J.__renderTarget=g,(!J.__webglTexture||g.depthTexture.image.width!==g.width||g.depthTexture.image.height!==g.height)&&(g.depthTexture.image.width=g.width,g.depthTexture.image.height=g.height,g.depthTexture.needsUpdate=!0),X){if(J.__webglInit===void 0&&(J.__webglInit=!0,g.depthTexture.addEventListener("dispose",w)),J.__webglTexture===void 0){J.__webglTexture=i.createTexture(),t.bindTexture(i.TEXTURE_CUBE_MAP,J.__webglTexture),Fe(i.TEXTURE_CUBE_MAP,g.depthTexture);let we=r.convert(g.depthTexture.format),j=r.convert(g.depthTexture.type),se;g.depthTexture.format===tn?se=i.DEPTH_COMPONENT24:g.depthTexture.format===On&&(se=i.DEPTH24_STENCIL8);for(let ge=0;ge<6;ge++)i.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+ge,0,se,g.width,g.height,0,we,j,null)}}else Y(g.depthTexture,0);let G=J.__webglTexture,Me=C(g),ne=X?i.TEXTURE_CUBE_MAP_POSITIVE_X+P:i.TEXTURE_2D,xe=g.depthTexture.format===On?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;if(g.depthTexture.format===tn)ct(g)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,xe,ne,G,0,Me):i.framebufferTexture2D(i.FRAMEBUFFER,xe,ne,G,0);else if(g.depthTexture.format===On)ct(g)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,xe,ne,G,0,Me):i.framebufferTexture2D(i.FRAMEBUFFER,xe,ne,G,0);else throw new Error("Unknown depthTexture format")}function ke(S){let g=n.get(S),P=S.isWebGLCubeRenderTarget===!0;if(g.__boundDepthTexture!==S.depthTexture){let X=S.depthTexture;if(g.__depthDisposeCallback&&g.__depthDisposeCallback(),X){let J=()=>{delete g.__boundDepthTexture,delete g.__depthDisposeCallback,X.removeEventListener("dispose",J)};X.addEventListener("dispose",J),g.__depthDisposeCallback=J}g.__boundDepthTexture=X}if(S.depthTexture&&!g.__autoAllocateDepthBuffer)if(P)for(let X=0;X<6;X++)_e(g.__webglFramebuffer[X],S,X);else{let X=S.texture.mipmaps;X&&X.length>0?_e(g.__webglFramebuffer[0],S,0):_e(g.__webglFramebuffer,S,0)}else if(P){g.__webglDepthbuffer=[];for(let X=0;X<6;X++)if(t.bindFramebuffer(i.FRAMEBUFFER,g.__webglFramebuffer[X]),g.__webglDepthbuffer[X]===void 0)g.__webglDepthbuffer[X]=i.createRenderbuffer(),Pe(g.__webglDepthbuffer[X],S,!1);else{let J=S.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,G=g.__webglDepthbuffer[X];i.bindRenderbuffer(i.RENDERBUFFER,G),i.framebufferRenderbuffer(i.FRAMEBUFFER,J,i.RENDERBUFFER,G)}}else{let X=S.texture.mipmaps;if(X&&X.length>0?t.bindFramebuffer(i.FRAMEBUFFER,g.__webglFramebuffer[0]):t.bindFramebuffer(i.FRAMEBUFFER,g.__webglFramebuffer),g.__webglDepthbuffer===void 0)g.__webglDepthbuffer=i.createRenderbuffer(),Pe(g.__webglDepthbuffer,S,!1);else{let J=S.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,G=g.__webglDepthbuffer;i.bindRenderbuffer(i.RENDERBUFFER,G),i.framebufferRenderbuffer(i.FRAMEBUFFER,J,i.RENDERBUFFER,G)}}t.bindFramebuffer(i.FRAMEBUFFER,null)}function pt(S,g,P){let X=n.get(S);g!==void 0&&pe(X.__webglFramebuffer,S,S.texture,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,0),P!==void 0&&ke(S)}function Ve(S){let g=S.texture,P=n.get(S),X=n.get(g);S.addEventListener("dispose",I);let J=S.textures,G=S.isWebGLCubeRenderTarget===!0,Me=J.length>1;if(Me||(X.__webglTexture===void 0&&(X.__webglTexture=i.createTexture()),X.__version=g.version,a.memory.textures++),G){P.__webglFramebuffer=[];for(let ne=0;ne<6;ne++)if(g.mipmaps&&g.mipmaps.length>0){P.__webglFramebuffer[ne]=[];for(let xe=0;xe<g.mipmaps.length;xe++)P.__webglFramebuffer[ne][xe]=i.createFramebuffer()}else P.__webglFramebuffer[ne]=i.createFramebuffer()}else{if(g.mipmaps&&g.mipmaps.length>0){P.__webglFramebuffer=[];for(let ne=0;ne<g.mipmaps.length;ne++)P.__webglFramebuffer[ne]=i.createFramebuffer()}else P.__webglFramebuffer=i.createFramebuffer();if(Me)for(let ne=0,xe=J.length;ne<xe;ne++){let we=n.get(J[ne]);we.__webglTexture===void 0&&(we.__webglTexture=i.createTexture(),a.memory.textures++)}if(S.samples>0&&ct(S)===!1){P.__webglMultisampledFramebuffer=i.createFramebuffer(),P.__webglColorRenderbuffer=[],t.bindFramebuffer(i.FRAMEBUFFER,P.__webglMultisampledFramebuffer);for(let ne=0;ne<J.length;ne++){let xe=J[ne];P.__webglColorRenderbuffer[ne]=i.createRenderbuffer(),i.bindRenderbuffer(i.RENDERBUFFER,P.__webglColorRenderbuffer[ne]);let we=r.convert(xe.format,xe.colorSpace),j=r.convert(xe.type),se=T(xe.internalFormat,we,j,xe.colorSpace,S.isXRRenderTarget===!0),ge=C(S);i.renderbufferStorageMultisample(i.RENDERBUFFER,ge,se,S.width,S.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+ne,i.RENDERBUFFER,P.__webglColorRenderbuffer[ne])}i.bindRenderbuffer(i.RENDERBUFFER,null),S.depthBuffer&&(P.__webglDepthRenderbuffer=i.createRenderbuffer(),Pe(P.__webglDepthRenderbuffer,S,!0)),t.bindFramebuffer(i.FRAMEBUFFER,null)}}if(G){t.bindTexture(i.TEXTURE_CUBE_MAP,X.__webglTexture),Fe(i.TEXTURE_CUBE_MAP,g);for(let ne=0;ne<6;ne++)if(g.mipmaps&&g.mipmaps.length>0)for(let xe=0;xe<g.mipmaps.length;xe++)pe(P.__webglFramebuffer[ne][xe],S,g,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+ne,xe);else pe(P.__webglFramebuffer[ne],S,g,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+ne,0);m(g)&&u(i.TEXTURE_CUBE_MAP),t.unbindTexture()}else if(Me){for(let ne=0,xe=J.length;ne<xe;ne++){let we=J[ne],j=n.get(we),se=i.TEXTURE_2D;(S.isWebGL3DRenderTarget||S.isWebGLArrayRenderTarget)&&(se=S.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(se,j.__webglTexture),Fe(se,we),pe(P.__webglFramebuffer,S,we,i.COLOR_ATTACHMENT0+ne,se,0),m(we)&&u(se)}t.unbindTexture()}else{let ne=i.TEXTURE_2D;if((S.isWebGL3DRenderTarget||S.isWebGLArrayRenderTarget)&&(ne=S.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(ne,X.__webglTexture),Fe(ne,g),g.mipmaps&&g.mipmaps.length>0)for(let xe=0;xe<g.mipmaps.length;xe++)pe(P.__webglFramebuffer[xe],S,g,i.COLOR_ATTACHMENT0,ne,xe);else pe(P.__webglFramebuffer,S,g,i.COLOR_ATTACHMENT0,ne,0);m(g)&&u(ne),t.unbindTexture()}S.depthBuffer&&ke(S)}function qe(S){let g=S.textures;for(let P=0,X=g.length;P<X;P++){let J=g[P];if(m(J)){let G=b(S),Me=n.get(J).__webglTexture;t.bindTexture(G,Me),u(G),t.unbindTexture()}}}let Ke=[],Ue=[];function lt(S){if(S.samples>0){if(ct(S)===!1){let g=S.textures,P=S.width,X=S.height,J=i.COLOR_BUFFER_BIT,G=S.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,Me=n.get(S),ne=g.length>1;if(ne)for(let we=0;we<g.length;we++)t.bindFramebuffer(i.FRAMEBUFFER,Me.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+we,i.RENDERBUFFER,null),t.bindFramebuffer(i.FRAMEBUFFER,Me.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+we,i.TEXTURE_2D,null,0);t.bindFramebuffer(i.READ_FRAMEBUFFER,Me.__webglMultisampledFramebuffer);let xe=S.texture.mipmaps;xe&&xe.length>0?t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Me.__webglFramebuffer[0]):t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Me.__webglFramebuffer);for(let we=0;we<g.length;we++){if(S.resolveDepthBuffer&&(S.depthBuffer&&(J|=i.DEPTH_BUFFER_BIT),S.stencilBuffer&&S.resolveStencilBuffer&&(J|=i.STENCIL_BUFFER_BIT)),ne){i.framebufferRenderbuffer(i.READ_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.RENDERBUFFER,Me.__webglColorRenderbuffer[we]);let j=n.get(g[we]).__webglTexture;i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,j,0)}i.blitFramebuffer(0,0,P,X,0,0,P,X,J,i.NEAREST),c===!0&&(Ke.length=0,Ue.length=0,Ke.push(i.COLOR_ATTACHMENT0+we),S.depthBuffer&&S.resolveDepthBuffer===!1&&(Ke.push(G),Ue.push(G),i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,Ue)),i.invalidateFramebuffer(i.READ_FRAMEBUFFER,Ke))}if(t.bindFramebuffer(i.READ_FRAMEBUFFER,null),t.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),ne)for(let we=0;we<g.length;we++){t.bindFramebuffer(i.FRAMEBUFFER,Me.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+we,i.RENDERBUFFER,Me.__webglColorRenderbuffer[we]);let j=n.get(g[we]).__webglTexture;t.bindFramebuffer(i.FRAMEBUFFER,Me.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+we,i.TEXTURE_2D,j,0)}t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Me.__webglMultisampledFramebuffer)}else if(S.depthBuffer&&S.resolveDepthBuffer===!1&&c){let g=S.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,[g])}}}function C(S){return Math.min(s.maxSamples,S.samples)}function ct(S){let g=n.get(S);return S.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&g.__useRenderToTexture!==!1}function We(S){let g=a.render.frame;h.get(S)!==g&&(h.set(S,g),S.update())}function je(S,g){let P=S.colorSpace,X=S.format,J=S.type;return S.isCompressedTexture===!0||S.isVideoTexture===!0||P!==Zn&&P!==Mn&&(ze.getTransfer(P)===Xe?(X!==Ht||J!==Bt)&&Ce("WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):Ee("WebGLTextures: Unsupported texture color space:",P)),g}function ve(S){return typeof HTMLImageElement<"u"&&S instanceof HTMLImageElement?(l.width=S.naturalWidth||S.width,l.height=S.naturalHeight||S.height):typeof VideoFrame<"u"&&S instanceof VideoFrame?(l.width=S.displayWidth,l.height=S.displayHeight):(l.width=S.width,l.height=S.height),l}this.allocateTextureUnit=z,this.resetTextureUnits=V,this.setTexture2D=Y,this.setTexture2DArray=k,this.setTexture3D=H,this.setTextureCube=$,this.rebindTextures=pt,this.setupRenderTarget=Ve,this.updateRenderTargetMipmap=qe,this.updateMultisampleRenderTarget=lt,this.setupDepthRenderbuffer=ke,this.setupFrameBufferTexture=pe,this.useMultisampledRTT=ct,this.isReversedDepthBuffer=function(){return t.buffers.depth.getReversed()}}function Ip(i,e){function t(n,s=Mn){let r,a=ze.getTransfer(s);if(n===Bt)return i.UNSIGNED_BYTE;if(n===mr)return i.UNSIGNED_SHORT_4_4_4_4;if(n===gr)return i.UNSIGNED_SHORT_5_5_5_1;if(n===ja)return i.UNSIGNED_INT_5_9_9_9_REV;if(n===eo)return i.UNSIGNED_INT_10F_11F_11F_REV;if(n===Ka)return i.BYTE;if(n===Qa)return i.SHORT;if(n===Ei)return i.UNSIGNED_SHORT;if(n===pr)return i.INT;if(n===$t)return i.UNSIGNED_INT;if(n===Kt)return i.FLOAT;if(n===on)return i.HALF_FLOAT;if(n===to)return i.ALPHA;if(n===no)return i.RGB;if(n===Ht)return i.RGBA;if(n===tn)return i.DEPTH_COMPONENT;if(n===On)return i.DEPTH_STENCIL;if(n===io)return i.RED;if(n===_r)return i.RED_INTEGER;if(n===ei)return i.RG;if(n===xr)return i.RG_INTEGER;if(n===vr)return i.RGBA_INTEGER;if(n===is||n===ss||n===rs||n===as)if(a===Xe)if(r=e.get("WEBGL_compressed_texture_s3tc_srgb"),r!==null){if(n===is)return r.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(n===ss)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(n===rs)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(n===as)return r.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(r=e.get("WEBGL_compressed_texture_s3tc"),r!==null){if(n===is)return r.COMPRESSED_RGB_S3TC_DXT1_EXT;if(n===ss)return r.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(n===rs)return r.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(n===as)return r.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(n===yr||n===Mr||n===Sr||n===br)if(r=e.get("WEBGL_compressed_texture_pvrtc"),r!==null){if(n===yr)return r.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(n===Mr)return r.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(n===Sr)return r.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(n===br)return r.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(n===Ar||n===Tr||n===Er||n===wr||n===Cr||n===Rr||n===Ir)if(r=e.get("WEBGL_compressed_texture_etc"),r!==null){if(n===Ar||n===Tr)return a===Xe?r.COMPRESSED_SRGB8_ETC2:r.COMPRESSED_RGB8_ETC2;if(n===Er)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:r.COMPRESSED_RGBA8_ETC2_EAC;if(n===wr)return r.COMPRESSED_R11_EAC;if(n===Cr)return r.COMPRESSED_SIGNED_R11_EAC;if(n===Rr)return r.COMPRESSED_RG11_EAC;if(n===Ir)return r.COMPRESSED_SIGNED_RG11_EAC}else return null;if(n===Pr||n===Lr||n===Dr||n===Ur||n===Nr||n===Fr||n===Or||n===Br||n===zr||n===Vr||n===kr||n===Gr||n===Hr||n===Wr)if(r=e.get("WEBGL_compressed_texture_astc"),r!==null){if(n===Pr)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:r.COMPRESSED_RGBA_ASTC_4x4_KHR;if(n===Lr)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:r.COMPRESSED_RGBA_ASTC_5x4_KHR;if(n===Dr)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:r.COMPRESSED_RGBA_ASTC_5x5_KHR;if(n===Ur)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:r.COMPRESSED_RGBA_ASTC_6x5_KHR;if(n===Nr)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:r.COMPRESSED_RGBA_ASTC_6x6_KHR;if(n===Fr)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:r.COMPRESSED_RGBA_ASTC_8x5_KHR;if(n===Or)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:r.COMPRESSED_RGBA_ASTC_8x6_KHR;if(n===Br)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:r.COMPRESSED_RGBA_ASTC_8x8_KHR;if(n===zr)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:r.COMPRESSED_RGBA_ASTC_10x5_KHR;if(n===Vr)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:r.COMPRESSED_RGBA_ASTC_10x6_KHR;if(n===kr)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:r.COMPRESSED_RGBA_ASTC_10x8_KHR;if(n===Gr)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:r.COMPRESSED_RGBA_ASTC_10x10_KHR;if(n===Hr)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:r.COMPRESSED_RGBA_ASTC_12x10_KHR;if(n===Wr)return a===Xe?r.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:r.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(n===Xr||n===qr||n===Yr)if(r=e.get("EXT_texture_compression_bptc"),r!==null){if(n===Xr)return a===Xe?r.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:r.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(n===qr)return r.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(n===Yr)return r.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(n===Zr||n===Jr||n===$r||n===Kr)if(r=e.get("EXT_texture_compression_rgtc"),r!==null){if(n===Zr)return r.COMPRESSED_RED_RGTC1_EXT;if(n===Jr)return r.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(n===$r)return r.COMPRESSED_RED_GREEN_RGTC2_EXT;if(n===Kr)return r.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return n===wi?i.UNSIGNED_INT_24_8:i[n]!==void 0?i[n]:null}return{convert:t}}var Pp=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,Lp=`
uniform sampler2DArray depthColor;
uniform float depthWidth;
uniform float depthHeight;

void main() {

	vec2 coord = vec2( gl_FragCoord.x / depthWidth, gl_FragCoord.y / depthHeight );

	if ( coord.x >= 1.0 ) {

		gl_FragDepth = texture( depthColor, vec3( coord.x - 1.0, coord.y, 1 ) ).r;

	} else {

		gl_FragDepth = texture( depthColor, vec3( coord.x, coord.y, 0 ) ).r;

	}

}`,To=class{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,t){if(this.texture===null){let n=new Ki(e.texture);(e.depthNear!==t.depthNear||e.depthFar!==t.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=n}}getMesh(e){if(this.texture!==null&&this.mesh===null){let t=e.cameras[0].viewport,n=new Ft({vertexShader:Pp,fragmentShader:Lp,uniforms:{depthColor:{value:this.texture},depthWidth:{value:t.z},depthHeight:{value:t.w}}});this.mesh=new Rt(new Kn(20,20),n)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}},Eo=class extends vn{constructor(e,t){super();let n=this,s=null,r=1,a=null,o="local-floor",c=1,l=null,h=null,f=null,p=null,d=null,_=null,y=typeof XRWebGLBinding<"u",m=new To,u={},b=t.getContextAttributes(),T=null,A=null,E=[],w=[],I=new Je,B=null,v=new yt;v.viewport=new ot;let M=new yt;M.viewport=new ot;let L=[v,M],V=new ir,z=null,W=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(q){let K=E[q];return K===void 0&&(K=new Ai,E[q]=K),K.getTargetRaySpace()},this.getControllerGrip=function(q){let K=E[q];return K===void 0&&(K=new Ai,E[q]=K),K.getGripSpace()},this.getHand=function(q){let K=E[q];return K===void 0&&(K=new Ai,E[q]=K),K.getHandSpace()};function Y(q){let K=w.indexOf(q.inputSource);if(K===-1)return;let pe=E[K];pe!==void 0&&(pe.update(q.inputSource,q.frame,l||a),pe.dispatchEvent({type:q.type,data:q.inputSource}))}function k(){s.removeEventListener("select",Y),s.removeEventListener("selectstart",Y),s.removeEventListener("selectend",Y),s.removeEventListener("squeeze",Y),s.removeEventListener("squeezestart",Y),s.removeEventListener("squeezeend",Y),s.removeEventListener("end",k),s.removeEventListener("inputsourceschange",H);for(let q=0;q<E.length;q++){let K=w[q];K!==null&&(w[q]=null,E[q].disconnect(K))}z=null,W=null,m.reset();for(let q in u)delete u[q];e.setRenderTarget(T),d=null,p=null,f=null,s=null,A=null,nt.stop(),n.isPresenting=!1,e.setPixelRatio(B),e.setSize(I.width,I.height,!1),n.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(q){r=q,n.isPresenting===!0&&Ce("WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(q){o=q,n.isPresenting===!0&&Ce("WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return l||a},this.setReferenceSpace=function(q){l=q},this.getBaseLayer=function(){return p!==null?p:d},this.getBinding=function(){return f===null&&y&&(f=new XRWebGLBinding(s,t)),f},this.getFrame=function(){return _},this.getSession=function(){return s},this.setSession=async function(q){if(s=q,s!==null){if(T=e.getRenderTarget(),s.addEventListener("select",Y),s.addEventListener("selectstart",Y),s.addEventListener("selectend",Y),s.addEventListener("squeeze",Y),s.addEventListener("squeezestart",Y),s.addEventListener("squeezeend",Y),s.addEventListener("end",k),s.addEventListener("inputsourceschange",H),b.xrCompatible!==!0&&await t.makeXRCompatible(),B=e.getPixelRatio(),e.getSize(I),y&&"createProjectionLayer"in XRWebGLBinding.prototype){let pe=null,Pe=null,_e=null;b.depth&&(_e=b.stencil?t.DEPTH24_STENCIL8:t.DEPTH_COMPONENT24,pe=b.stencil?On:tn,Pe=b.stencil?wi:$t);let ke={colorFormat:t.RGBA8,depthFormat:_e,scaleFactor:r};f=this.getBinding(),p=f.createProjectionLayer(ke),s.updateRenderState({layers:[p]}),e.setPixelRatio(1),e.setSize(p.textureWidth,p.textureHeight,!1),A=new Nt(p.textureWidth,p.textureHeight,{format:Ht,type:Bt,depthTexture:new Ln(p.textureWidth,p.textureHeight,Pe,void 0,void 0,void 0,void 0,void 0,void 0,pe),stencilBuffer:b.stencil,colorSpace:e.outputColorSpace,samples:b.antialias?4:0,resolveDepthBuffer:p.ignoreDepthValues===!1,resolveStencilBuffer:p.ignoreDepthValues===!1})}else{let pe={antialias:b.antialias,alpha:!0,depth:b.depth,stencil:b.stencil,framebufferScaleFactor:r};d=new XRWebGLLayer(s,t,pe),s.updateRenderState({baseLayer:d}),e.setPixelRatio(1),e.setSize(d.framebufferWidth,d.framebufferHeight,!1),A=new Nt(d.framebufferWidth,d.framebufferHeight,{format:Ht,type:Bt,colorSpace:e.outputColorSpace,stencilBuffer:b.stencil,resolveDepthBuffer:d.ignoreDepthValues===!1,resolveStencilBuffer:d.ignoreDepthValues===!1})}A.isXRRenderTarget=!0,this.setFoveation(c),l=null,a=await s.requestReferenceSpace(o),nt.setContext(s),nt.start(),n.isPresenting=!0,n.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(s!==null)return s.environmentBlendMode},this.getDepthTexture=function(){return m.getDepthTexture()};function H(q){for(let K=0;K<q.removed.length;K++){let pe=q.removed[K],Pe=w.indexOf(pe);Pe>=0&&(w[Pe]=null,E[Pe].disconnect(pe))}for(let K=0;K<q.added.length;K++){let pe=q.added[K],Pe=w.indexOf(pe);if(Pe===-1){for(let ke=0;ke<E.length;ke++)if(ke>=w.length){w.push(pe),Pe=ke;break}else if(w[ke]===null){w[ke]=pe,Pe=ke;break}if(Pe===-1)break}let _e=E[Pe];_e&&_e.connect(pe)}}let $=new F,he=new F;function ae(q,K,pe){$.setFromMatrixPosition(K.matrixWorld),he.setFromMatrixPosition(pe.matrixWorld);let Pe=$.distanceTo(he),_e=K.projectionMatrix.elements,ke=pe.projectionMatrix.elements,pt=_e[14]/(_e[10]-1),Ve=_e[14]/(_e[10]+1),qe=(_e[9]+1)/_e[5],Ke=(_e[9]-1)/_e[5],Ue=(_e[8]-1)/_e[0],lt=(ke[8]+1)/ke[0],C=pt*Ue,ct=pt*lt,We=Pe/(-Ue+lt),je=We*-Ue;if(K.matrixWorld.decompose(q.position,q.quaternion,q.scale),q.translateX(je),q.translateZ(We),q.matrixWorld.compose(q.position,q.quaternion,q.scale),q.matrixWorldInverse.copy(q.matrixWorld).invert(),_e[10]===-1)q.projectionMatrix.copy(K.projectionMatrix),q.projectionMatrixInverse.copy(K.projectionMatrixInverse);else{let ve=pt+We,S=Ve+We,g=C-je,P=ct+(Pe-je),X=qe*Ve/S*ve,J=Ke*Ve/S*ve;q.projectionMatrix.makePerspective(g,P,X,J,ve,S),q.projectionMatrixInverse.copy(q.projectionMatrix).invert()}}function ue(q,K){K===null?q.matrixWorld.copy(q.matrix):q.matrixWorld.multiplyMatrices(K.matrixWorld,q.matrix),q.matrixWorldInverse.copy(q.matrixWorld).invert()}this.updateCamera=function(q){if(s===null)return;let K=q.near,pe=q.far;m.texture!==null&&(m.depthNear>0&&(K=m.depthNear),m.depthFar>0&&(pe=m.depthFar)),V.near=M.near=v.near=K,V.far=M.far=v.far=pe,(z!==V.near||W!==V.far)&&(s.updateRenderState({depthNear:V.near,depthFar:V.far}),z=V.near,W=V.far),V.layers.mask=q.layers.mask|6,v.layers.mask=V.layers.mask&3,M.layers.mask=V.layers.mask&5;let Pe=q.parent,_e=V.cameras;ue(V,Pe);for(let ke=0;ke<_e.length;ke++)ue(_e[ke],Pe);_e.length===2?ae(V,v,M):V.projectionMatrix.copy(v.projectionMatrix),Fe(q,V,Pe)};function Fe(q,K,pe){pe===null?q.matrix.copy(K.matrixWorld):(q.matrix.copy(pe.matrixWorld),q.matrix.invert(),q.matrix.multiply(K.matrixWorld)),q.matrix.decompose(q.position,q.quaternion,q.scale),q.updateMatrixWorld(!0),q.projectionMatrix.copy(K.projectionMatrix),q.projectionMatrixInverse.copy(K.projectionMatrixInverse),q.isPerspectiveCamera&&(q.fov=Os*2*Math.atan(1/q.projectionMatrix.elements[5]),q.zoom=1)}this.getCamera=function(){return V},this.getFoveation=function(){if(!(p===null&&d===null))return c},this.setFoveation=function(q){c=q,p!==null&&(p.fixedFoveation=q),d!==null&&d.fixedFoveation!==void 0&&(d.fixedFoveation=q)},this.hasDepthSensing=function(){return m.texture!==null},this.getDepthSensingMesh=function(){return m.getMesh(V)},this.getCameraTexture=function(q){return u[q]};let De=null;function st(q,K){if(h=K.getViewerPose(l||a),_=K,h!==null){let pe=h.views;d!==null&&(e.setRenderTargetFramebuffer(A,d.framebuffer),e.setRenderTarget(A));let Pe=!1;pe.length!==V.cameras.length&&(V.cameras.length=0,Pe=!0);for(let Ve=0;Ve<pe.length;Ve++){let qe=pe[Ve],Ke=null;if(d!==null)Ke=d.getViewport(qe);else{let lt=f.getViewSubImage(p,qe);Ke=lt.viewport,Ve===0&&(e.setRenderTargetTextures(A,lt.colorTexture,lt.depthStencilTexture),e.setRenderTarget(A))}let Ue=L[Ve];Ue===void 0&&(Ue=new yt,Ue.layers.enable(Ve),Ue.viewport=new ot,L[Ve]=Ue),Ue.matrix.fromArray(qe.transform.matrix),Ue.matrix.decompose(Ue.position,Ue.quaternion,Ue.scale),Ue.projectionMatrix.fromArray(qe.projectionMatrix),Ue.projectionMatrixInverse.copy(Ue.projectionMatrix).invert(),Ue.viewport.set(Ke.x,Ke.y,Ke.width,Ke.height),Ve===0&&(V.matrix.copy(Ue.matrix),V.matrix.decompose(V.position,V.quaternion,V.scale)),Pe===!0&&V.cameras.push(Ue)}let _e=s.enabledFeatures;if(_e&&_e.includes("depth-sensing")&&s.depthUsage=="gpu-optimized"&&y){f=n.getBinding();let Ve=f.getDepthInformation(pe[0]);Ve&&Ve.isValid&&Ve.texture&&m.init(Ve,s.renderState)}if(_e&&_e.includes("camera-access")&&y){e.state.unbindTexture(),f=n.getBinding();for(let Ve=0;Ve<pe.length;Ve++){let qe=pe[Ve].camera;if(qe){let Ke=u[qe];Ke||(Ke=new Ki,u[qe]=Ke);let Ue=f.getCameraImage(qe);Ke.sourceTexture=Ue}}}}for(let pe=0;pe<E.length;pe++){let Pe=w[pe],_e=E[pe];Pe!==null&&_e!==void 0&&_e.update(Pe,K,l||a)}De&&De(q,K),K.detectedPlanes&&n.dispatchEvent({type:"planesdetected",data:K}),_=null}let nt=new sc;nt.setAnimationLoop(st),this.setAnimationLoop=function(q){De=q},this.dispose=function(){}}},ii=new nn,Dp=new ut;function Up(i,e){function t(m,u){m.matrixAutoUpdate===!0&&m.updateMatrix(),u.value.copy(m.matrix)}function n(m,u){u.color.getRGB(m.fogColor.value,oo(i)),u.isFog?(m.fogNear.value=u.near,m.fogFar.value=u.far):u.isFogExp2&&(m.fogDensity.value=u.density)}function s(m,u,b,T,A){u.isMeshBasicMaterial||u.isMeshLambertMaterial?r(m,u):u.isMeshToonMaterial?(r(m,u),f(m,u)):u.isMeshPhongMaterial?(r(m,u),h(m,u)):u.isMeshStandardMaterial?(r(m,u),p(m,u),u.isMeshPhysicalMaterial&&d(m,u,A)):u.isMeshMatcapMaterial?(r(m,u),_(m,u)):u.isMeshDepthMaterial?r(m,u):u.isMeshDistanceMaterial?(r(m,u),y(m,u)):u.isMeshNormalMaterial?r(m,u):u.isLineBasicMaterial?(a(m,u),u.isLineDashedMaterial&&o(m,u)):u.isPointsMaterial?c(m,u,b,T):u.isSpriteMaterial?l(m,u):u.isShadowMaterial?(m.color.value.copy(u.color),m.opacity.value=u.opacity):u.isShaderMaterial&&(u.uniformsNeedUpdate=!1)}function r(m,u){m.opacity.value=u.opacity,u.color&&m.diffuse.value.copy(u.color),u.emissive&&m.emissive.value.copy(u.emissive).multiplyScalar(u.emissiveIntensity),u.map&&(m.map.value=u.map,t(u.map,m.mapTransform)),u.alphaMap&&(m.alphaMap.value=u.alphaMap,t(u.alphaMap,m.alphaMapTransform)),u.bumpMap&&(m.bumpMap.value=u.bumpMap,t(u.bumpMap,m.bumpMapTransform),m.bumpScale.value=u.bumpScale,u.side===Tt&&(m.bumpScale.value*=-1)),u.normalMap&&(m.normalMap.value=u.normalMap,t(u.normalMap,m.normalMapTransform),m.normalScale.value.copy(u.normalScale),u.side===Tt&&m.normalScale.value.negate()),u.displacementMap&&(m.displacementMap.value=u.displacementMap,t(u.displacementMap,m.displacementMapTransform),m.displacementScale.value=u.displacementScale,m.displacementBias.value=u.displacementBias),u.emissiveMap&&(m.emissiveMap.value=u.emissiveMap,t(u.emissiveMap,m.emissiveMapTransform)),u.specularMap&&(m.specularMap.value=u.specularMap,t(u.specularMap,m.specularMapTransform)),u.alphaTest>0&&(m.alphaTest.value=u.alphaTest);let b=e.get(u),T=b.envMap,A=b.envMapRotation;T&&(m.envMap.value=T,ii.copy(A),ii.x*=-1,ii.y*=-1,ii.z*=-1,T.isCubeTexture&&T.isRenderTargetTexture===!1&&(ii.y*=-1,ii.z*=-1),m.envMapRotation.value.setFromMatrix4(Dp.makeRotationFromEuler(ii)),m.flipEnvMap.value=T.isCubeTexture&&T.isRenderTargetTexture===!1?-1:1,m.reflectivity.value=u.reflectivity,m.ior.value=u.ior,m.refractionRatio.value=u.refractionRatio),u.lightMap&&(m.lightMap.value=u.lightMap,m.lightMapIntensity.value=u.lightMapIntensity,t(u.lightMap,m.lightMapTransform)),u.aoMap&&(m.aoMap.value=u.aoMap,m.aoMapIntensity.value=u.aoMapIntensity,t(u.aoMap,m.aoMapTransform))}function a(m,u){m.diffuse.value.copy(u.color),m.opacity.value=u.opacity,u.map&&(m.map.value=u.map,t(u.map,m.mapTransform))}function o(m,u){m.dashSize.value=u.dashSize,m.totalSize.value=u.dashSize+u.gapSize,m.scale.value=u.scale}function c(m,u,b,T){m.diffuse.value.copy(u.color),m.opacity.value=u.opacity,m.size.value=u.size*b,m.scale.value=T*.5,u.map&&(m.map.value=u.map,t(u.map,m.uvTransform)),u.alphaMap&&(m.alphaMap.value=u.alphaMap,t(u.alphaMap,m.alphaMapTransform)),u.alphaTest>0&&(m.alphaTest.value=u.alphaTest)}function l(m,u){m.diffuse.value.copy(u.color),m.opacity.value=u.opacity,m.rotation.value=u.rotation,u.map&&(m.map.value=u.map,t(u.map,m.mapTransform)),u.alphaMap&&(m.alphaMap.value=u.alphaMap,t(u.alphaMap,m.alphaMapTransform)),u.alphaTest>0&&(m.alphaTest.value=u.alphaTest)}function h(m,u){m.specular.value.copy(u.specular),m.shininess.value=Math.max(u.shininess,1e-4)}function f(m,u){u.gradientMap&&(m.gradientMap.value=u.gradientMap)}function p(m,u){m.metalness.value=u.metalness,u.metalnessMap&&(m.metalnessMap.value=u.metalnessMap,t(u.metalnessMap,m.metalnessMapTransform)),m.roughness.value=u.roughness,u.roughnessMap&&(m.roughnessMap.value=u.roughnessMap,t(u.roughnessMap,m.roughnessMapTransform)),u.envMap&&(m.envMapIntensity.value=u.envMapIntensity)}function d(m,u,b){m.ior.value=u.ior,u.sheen>0&&(m.sheenColor.value.copy(u.sheenColor).multiplyScalar(u.sheen),m.sheenRoughness.value=u.sheenRoughness,u.sheenColorMap&&(m.sheenColorMap.value=u.sheenColorMap,t(u.sheenColorMap,m.sheenColorMapTransform)),u.sheenRoughnessMap&&(m.sheenRoughnessMap.value=u.sheenRoughnessMap,t(u.sheenRoughnessMap,m.sheenRoughnessMapTransform))),u.clearcoat>0&&(m.clearcoat.value=u.clearcoat,m.clearcoatRoughness.value=u.clearcoatRoughness,u.clearcoatMap&&(m.clearcoatMap.value=u.clearcoatMap,t(u.clearcoatMap,m.clearcoatMapTransform)),u.clearcoatRoughnessMap&&(m.clearcoatRoughnessMap.value=u.clearcoatRoughnessMap,t(u.clearcoatRoughnessMap,m.clearcoatRoughnessMapTransform)),u.clearcoatNormalMap&&(m.clearcoatNormalMap.value=u.clearcoatNormalMap,t(u.clearcoatNormalMap,m.clearcoatNormalMapTransform),m.clearcoatNormalScale.value.copy(u.clearcoatNormalScale),u.side===Tt&&m.clearcoatNormalScale.value.negate())),u.dispersion>0&&(m.dispersion.value=u.dispersion),u.iridescence>0&&(m.iridescence.value=u.iridescence,m.iridescenceIOR.value=u.iridescenceIOR,m.iridescenceThicknessMinimum.value=u.iridescenceThicknessRange[0],m.iridescenceThicknessMaximum.value=u.iridescenceThicknessRange[1],u.iridescenceMap&&(m.iridescenceMap.value=u.iridescenceMap,t(u.iridescenceMap,m.iridescenceMapTransform)),u.iridescenceThicknessMap&&(m.iridescenceThicknessMap.value=u.iridescenceThicknessMap,t(u.iridescenceThicknessMap,m.iridescenceThicknessMapTransform))),u.transmission>0&&(m.transmission.value=u.transmission,m.transmissionSamplerMap.value=b.texture,m.transmissionSamplerSize.value.set(b.width,b.height),u.transmissionMap&&(m.transmissionMap.value=u.transmissionMap,t(u.transmissionMap,m.transmissionMapTransform)),m.thickness.value=u.thickness,u.thicknessMap&&(m.thicknessMap.value=u.thicknessMap,t(u.thicknessMap,m.thicknessMapTransform)),m.attenuationDistance.value=u.attenuationDistance,m.attenuationColor.value.copy(u.attenuationColor)),u.anisotropy>0&&(m.anisotropyVector.value.set(u.anisotropy*Math.cos(u.anisotropyRotation),u.anisotropy*Math.sin(u.anisotropyRotation)),u.anisotropyMap&&(m.anisotropyMap.value=u.anisotropyMap,t(u.anisotropyMap,m.anisotropyMapTransform))),m.specularIntensity.value=u.specularIntensity,m.specularColor.value.copy(u.specularColor),u.specularColorMap&&(m.specularColorMap.value=u.specularColorMap,t(u.specularColorMap,m.specularColorMapTransform)),u.specularIntensityMap&&(m.specularIntensityMap.value=u.specularIntensityMap,t(u.specularIntensityMap,m.specularIntensityMapTransform))}function _(m,u){u.matcap&&(m.matcap.value=u.matcap)}function y(m,u){let b=e.get(u).light;m.referencePosition.value.setFromMatrixPosition(b.matrixWorld),m.nearDistance.value=b.shadow.camera.near,m.farDistance.value=b.shadow.camera.far}return{refreshFogUniforms:n,refreshMaterialUniforms:s}}function Np(i,e,t,n){let s={},r={},a=[],o=i.getParameter(i.MAX_UNIFORM_BUFFER_BINDINGS);function c(b,T){let A=T.program;n.uniformBlockBinding(b,A)}function l(b,T){let A=s[b.id];A===void 0&&(_(b),A=h(b),s[b.id]=A,b.addEventListener("dispose",m));let E=T.program;n.updateUBOMapping(b,E);let w=e.render.frame;r[b.id]!==w&&(p(b),r[b.id]=w)}function h(b){let T=f();b.__bindingPointIndex=T;let A=i.createBuffer(),E=b.__size,w=b.usage;return i.bindBuffer(i.UNIFORM_BUFFER,A),i.bufferData(i.UNIFORM_BUFFER,E,w),i.bindBuffer(i.UNIFORM_BUFFER,null),i.bindBufferBase(i.UNIFORM_BUFFER,T,A),A}function f(){for(let b=0;b<o;b++)if(a.indexOf(b)===-1)return a.push(b),b;return Ee("WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function p(b){let T=s[b.id],A=b.uniforms,E=b.__cache;i.bindBuffer(i.UNIFORM_BUFFER,T);for(let w=0,I=A.length;w<I;w++){let B=Array.isArray(A[w])?A[w]:[A[w]];for(let v=0,M=B.length;v<M;v++){let L=B[v];if(d(L,w,v,E)===!0){let V=L.__offset,z=Array.isArray(L.value)?L.value:[L.value],W=0;for(let Y=0;Y<z.length;Y++){let k=z[Y],H=y(k);typeof k=="number"||typeof k=="boolean"?(L.__data[0]=k,i.bufferSubData(i.UNIFORM_BUFFER,V+W,L.__data)):k.isMatrix3?(L.__data[0]=k.elements[0],L.__data[1]=k.elements[1],L.__data[2]=k.elements[2],L.__data[3]=0,L.__data[4]=k.elements[3],L.__data[5]=k.elements[4],L.__data[6]=k.elements[5],L.__data[7]=0,L.__data[8]=k.elements[6],L.__data[9]=k.elements[7],L.__data[10]=k.elements[8],L.__data[11]=0):(k.toArray(L.__data,W),W+=H.storage/Float32Array.BYTES_PER_ELEMENT)}i.bufferSubData(i.UNIFORM_BUFFER,V,L.__data)}}}i.bindBuffer(i.UNIFORM_BUFFER,null)}function d(b,T,A,E){let w=b.value,I=T+"_"+A;if(E[I]===void 0)return typeof w=="number"||typeof w=="boolean"?E[I]=w:E[I]=w.clone(),!0;{let B=E[I];if(typeof w=="number"||typeof w=="boolean"){if(B!==w)return E[I]=w,!0}else if(B.equals(w)===!1)return B.copy(w),!0}return!1}function _(b){let T=b.uniforms,A=0,E=16;for(let I=0,B=T.length;I<B;I++){let v=Array.isArray(T[I])?T[I]:[T[I]];for(let M=0,L=v.length;M<L;M++){let V=v[M],z=Array.isArray(V.value)?V.value:[V.value];for(let W=0,Y=z.length;W<Y;W++){let k=z[W],H=y(k),$=A%E,he=$%H.boundary,ae=$+he;A+=he,ae!==0&&E-ae<H.storage&&(A+=E-ae),V.__data=new Float32Array(H.storage/Float32Array.BYTES_PER_ELEMENT),V.__offset=A,A+=H.storage}}}let w=A%E;return w>0&&(A+=E-w),b.__size=A,b.__cache={},this}function y(b){let T={boundary:0,storage:0};return typeof b=="number"||typeof b=="boolean"?(T.boundary=4,T.storage=4):b.isVector2?(T.boundary=8,T.storage=8):b.isVector3||b.isColor?(T.boundary=16,T.storage=12):b.isVector4?(T.boundary=16,T.storage=16):b.isMatrix3?(T.boundary=48,T.storage=48):b.isMatrix4?(T.boundary=64,T.storage=64):b.isTexture?Ce("WebGLRenderer: Texture samplers can not be part of an uniforms group."):Ce("WebGLRenderer: Unsupported uniform value type.",b),T}function m(b){let T=b.target;T.removeEventListener("dispose",m);let A=a.indexOf(T.__bindingPointIndex);a.splice(A,1),i.deleteBuffer(s[T.id]),delete s[T.id],delete r[T.id]}function u(){for(let b in s)i.deleteBuffer(s[b]);a=[],s={},r={}}return{bind:c,update:l,dispose:u}}var Fp=new Uint16Array([12469,15057,12620,14925,13266,14620,13807,14376,14323,13990,14545,13625,14713,13328,14840,12882,14931,12528,14996,12233,15039,11829,15066,11525,15080,11295,15085,10976,15082,10705,15073,10495,13880,14564,13898,14542,13977,14430,14158,14124,14393,13732,14556,13410,14702,12996,14814,12596,14891,12291,14937,11834,14957,11489,14958,11194,14943,10803,14921,10506,14893,10278,14858,9960,14484,14039,14487,14025,14499,13941,14524,13740,14574,13468,14654,13106,14743,12678,14818,12344,14867,11893,14889,11509,14893,11180,14881,10751,14852,10428,14812,10128,14765,9754,14712,9466,14764,13480,14764,13475,14766,13440,14766,13347,14769,13070,14786,12713,14816,12387,14844,11957,14860,11549,14868,11215,14855,10751,14825,10403,14782,10044,14729,9651,14666,9352,14599,9029,14967,12835,14966,12831,14963,12804,14954,12723,14936,12564,14917,12347,14900,11958,14886,11569,14878,11247,14859,10765,14828,10401,14784,10011,14727,9600,14660,9289,14586,8893,14508,8533,15111,12234,15110,12234,15104,12216,15092,12156,15067,12010,15028,11776,14981,11500,14942,11205,14902,10752,14861,10393,14812,9991,14752,9570,14682,9252,14603,8808,14519,8445,14431,8145,15209,11449,15208,11451,15202,11451,15190,11438,15163,11384,15117,11274,15055,10979,14994,10648,14932,10343,14871,9936,14803,9532,14729,9218,14645,8742,14556,8381,14461,8020,14365,7603,15273,10603,15272,10607,15267,10619,15256,10631,15231,10614,15182,10535,15118,10389,15042,10167,14963,9787,14883,9447,14800,9115,14710,8665,14615,8318,14514,7911,14411,7507,14279,7198,15314,9675,15313,9683,15309,9712,15298,9759,15277,9797,15229,9773,15166,9668,15084,9487,14995,9274,14898,8910,14800,8539,14697,8234,14590,7790,14479,7409,14367,7067,14178,6621,15337,8619,15337,8631,15333,8677,15325,8769,15305,8871,15264,8940,15202,8909,15119,8775,15022,8565,14916,8328,14804,8009,14688,7614,14569,7287,14448,6888,14321,6483,14088,6171,15350,7402,15350,7419,15347,7480,15340,7613,15322,7804,15287,7973,15229,8057,15148,8012,15046,7846,14933,7611,14810,7357,14682,7069,14552,6656,14421,6316,14251,5948,14007,5528,15356,5942,15356,5977,15353,6119,15348,6294,15332,6551,15302,6824,15249,7044,15171,7122,15070,7050,14949,6861,14818,6611,14679,6349,14538,6067,14398,5651,14189,5311,13935,4958,15359,4123,15359,4153,15356,4296,15353,4646,15338,5160,15311,5508,15263,5829,15188,6042,15088,6094,14966,6001,14826,5796,14678,5543,14527,5287,14377,4985,14133,4586,13869,4257,15360,1563,15360,1642,15358,2076,15354,2636,15341,3350,15317,4019,15273,4429,15203,4732,15105,4911,14981,4932,14836,4818,14679,4621,14517,4386,14359,4156,14083,3795,13808,3437,15360,122,15360,137,15358,285,15355,636,15344,1274,15322,2177,15281,2765,15215,3223,15120,3451,14995,3569,14846,3567,14681,3466,14511,3305,14344,3121,14037,2800,13753,2467,15360,0,15360,1,15359,21,15355,89,15346,253,15325,479,15287,796,15225,1148,15133,1492,15008,1749,14856,1882,14685,1886,14506,1783,14324,1608,13996,1398,13702,1183]),ln=null;function Op(){return ln===null&&(ln=new Hs(Fp,16,16,ei,on),ln.name="DFG_LUT",ln.minFilter=_t,ln.magFilter=_t,ln.wrapS=en,ln.wrapT=en,ln.generateMipmaps=!1,ln.needsUpdate=!0),ln}var ia=class{constructor(e={}){let{canvas:t=Pl(),context:n=null,depth:s=!0,stencil:r=!1,alpha:a=!1,antialias:o=!1,premultipliedAlpha:c=!0,preserveDrawingBuffer:l=!1,powerPreference:h="default",failIfMajorPerformanceCaveat:f=!1,reversedDepthBuffer:p=!1,outputBufferType:d=Bt}=e;this.isWebGLRenderer=!0;let _;if(n!==null){if(typeof WebGLRenderingContext<"u"&&n instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");_=n.getContextAttributes().alpha}else _=a;let y=d,m=new Set([vr,xr,_r]),u=new Set([Bt,$t,Ei,wi,mr,gr]),b=new Uint32Array(4),T=new Int32Array(4),A=null,E=null,w=[],I=[],B=null;this.domElement=t,this.debug={checkShaderErrors:!0,onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=Jt,this.toneMappingExposure=1,this.transmissionResolutionScale=1;let v=this,M=!1;this._outputColorSpace=bt;let L=0,V=0,z=null,W=-1,Y=null,k=new ot,H=new ot,$=null,he=new He(0),ae=0,ue=t.width,Fe=t.height,De=1,st=null,nt=null,q=new ot(0,0,ue,Fe),K=new ot(0,0,ue,Fe),pe=!1,Pe=new Ji,_e=!1,ke=!1,pt=new ut,Ve=new F,qe=new ot,Ke={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0},Ue=!1;function lt(){return z===null?De:1}let C=n;function ct(x,D){return t.getContext(x,D)}try{let x={alpha:!0,depth:s,stencil:r,antialias:o,premultipliedAlpha:c,preserveDrawingBuffer:l,powerPreference:h,failIfMajorPerformanceCaveat:f};if("setAttribute"in t&&t.setAttribute("data-engine",`three.js r${"182"}`),t.addEventListener("webglcontextlost",Re,!1),t.addEventListener("webglcontextrestored",et,!1),t.addEventListener("webglcontextcreationerror",Ye,!1),C===null){let D="webgl2";if(C=ct(D,x),C===null)throw ct(D)?new Error("Error creating WebGL context with your selected attributes."):new Error("Error creating WebGL context.")}}catch(x){throw Ee("WebGLRenderer: "+x.message),x}let We,je,ve,S,g,P,X,J,G,Me,ne,xe,we,j,se,ge,ye,ie,Ne,R,ce,ee,de,Q;function Z(){We=new Hd(C),We.init(),ee=new Ip(C,We),je=new Ud(C,We,e,ee),ve=new Cp(C,We),je.reversedDepthBuffer&&p&&ve.buffers.depth.setReversed(!0),S=new qd(C),g=new fp,P=new Rp(C,We,ve,g,je,ee,S),X=new Fd(v),J=new Gd(v),G=new $c(C),de=new Ld(C,G),Me=new Wd(C,G,S,de),ne=new Zd(C,Me,G,S),Ne=new Yd(C,je,P),ge=new Nd(g),xe=new dp(v,X,J,We,je,de,ge),we=new Up(v,g),j=new mp,se=new Mp(We),ie=new Pd(v,X,J,ve,ne,_,c),ye=new Ep(v,ne,je),Q=new Np(C,S,je,ve),R=new Dd(C,We,S),ce=new Xd(C,We,S),S.programs=xe.programs,v.capabilities=je,v.extensions=We,v.properties=g,v.renderLists=j,v.shadowMap=ye,v.state=ve,v.info=S}Z(),y!==Bt&&(B=new $d(y,t.width,t.height,s,r));let te=new Eo(v,C);this.xr=te,this.getContext=function(){return C},this.getContextAttributes=function(){return C.getContextAttributes()},this.forceContextLoss=function(){let x=We.get("WEBGL_lose_context");x&&x.loseContext()},this.forceContextRestore=function(){let x=We.get("WEBGL_lose_context");x&&x.restoreContext()},this.getPixelRatio=function(){return De},this.setPixelRatio=function(x){x!==void 0&&(De=x,this.setSize(ue,Fe,!1))},this.getSize=function(x){return x.set(ue,Fe)},this.setSize=function(x,D,O=!0){if(te.isPresenting){Ce("WebGLRenderer: Can't change size while VR device is presenting.");return}ue=x,Fe=D,t.width=Math.floor(x*De),t.height=Math.floor(D*De),O===!0&&(t.style.width=x+"px",t.style.height=D+"px"),B!==null&&B.setSize(t.width,t.height),this.setViewport(0,0,x,D)},this.getDrawingBufferSize=function(x){return x.set(ue*De,Fe*De).floor()},this.setDrawingBufferSize=function(x,D,O){ue=x,Fe=D,De=O,t.width=Math.floor(x*O),t.height=Math.floor(D*O),this.setViewport(0,0,x,D)},this.setEffects=function(x){if(y===Bt){console.error("THREE.WebGLRenderer: setEffects() requires outputBufferType set to HalfFloatType or FloatType.");return}if(x){for(let D=0;D<x.length;D++)if(x[D].isOutputPass===!0){console.warn("THREE.WebGLRenderer: OutputPass is not needed in setEffects(). Tone mapping and color space conversion are applied automatically.");break}}B.setEffects(x||[])},this.getCurrentViewport=function(x){return x.copy(k)},this.getViewport=function(x){return x.copy(q)},this.setViewport=function(x,D,O,N){x.isVector4?q.set(x.x,x.y,x.z,x.w):q.set(x,D,O,N),ve.viewport(k.copy(q).multiplyScalar(De).round())},this.getScissor=function(x){return x.copy(K)},this.setScissor=function(x,D,O,N){x.isVector4?K.set(x.x,x.y,x.z,x.w):K.set(x,D,O,N),ve.scissor(H.copy(K).multiplyScalar(De).round())},this.getScissorTest=function(){return pe},this.setScissorTest=function(x){ve.setScissorTest(pe=x)},this.setOpaqueSort=function(x){st=x},this.setTransparentSort=function(x){nt=x},this.getClearColor=function(x){return x.copy(ie.getClearColor())},this.setClearColor=function(){ie.setClearColor(...arguments)},this.getClearAlpha=function(){return ie.getClearAlpha()},this.setClearAlpha=function(){ie.setClearAlpha(...arguments)},this.clear=function(x=!0,D=!0,O=!0){let N=0;if(x){let U=!1;if(z!==null){let re=z.texture.format;U=m.has(re)}if(U){let re=z.texture.type,fe=u.has(re),le=ie.getClearColor(),me=ie.getClearAlpha(),Se=le.r,Te=le.g,be=le.b;fe?(b[0]=Se,b[1]=Te,b[2]=be,b[3]=me,C.clearBufferuiv(C.COLOR,0,b)):(T[0]=Se,T[1]=Te,T[2]=be,T[3]=me,C.clearBufferiv(C.COLOR,0,T))}else N|=C.COLOR_BUFFER_BIT}D&&(N|=C.DEPTH_BUFFER_BIT),O&&(N|=C.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),C.clear(N)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.dispose=function(){t.removeEventListener("webglcontextlost",Re,!1),t.removeEventListener("webglcontextrestored",et,!1),t.removeEventListener("webglcontextcreationerror",Ye,!1),ie.dispose(),j.dispose(),se.dispose(),g.dispose(),X.dispose(),J.dispose(),ne.dispose(),de.dispose(),Q.dispose(),xe.dispose(),te.dispose(),te.removeEventListener("sessionstart",Co),te.removeEventListener("sessionend",Ro),zn.stop()};function Re(x){x.preventDefault(),ao("WebGLRenderer: Context Lost."),M=!0}function et(){ao("WebGLRenderer: Context Restored."),M=!1;let x=S.autoReset,D=ye.enabled,O=ye.autoUpdate,N=ye.needsUpdate,U=ye.type;Z(),S.autoReset=x,ye.enabled=D,ye.autoUpdate=O,ye.needsUpdate=N,ye.type=U}function Ye(x){Ee("WebGLRenderer: A WebGL context could not be created. Reason: ",x.statusMessage)}function Qt(x){let D=x.target;D.removeEventListener("dispose",Qt),hn(D)}function hn(x){cc(x),g.remove(x)}function cc(x){let D=g.get(x).programs;D!==void 0&&(D.forEach(function(O){xe.releaseProgram(O)}),x.isShaderMaterial&&xe.releaseShaderCache(x))}this.renderBufferDirect=function(x,D,O,N,U,re){D===null&&(D=Ke);let fe=U.isMesh&&U.matrixWorld.determinant()<0,le=uc(x,D,O,N,U);ve.setMaterial(N,fe);let me=O.index,Se=1;if(N.wireframe===!0){if(me=Me.getWireframeAttribute(O),me===void 0)return;Se=2}let Te=O.drawRange,be=O.attributes.position,Oe=Te.start*Se,$e=(Te.start+Te.count)*Se;re!==null&&(Oe=Math.max(Oe,re.start*Se),$e=Math.min($e,(re.start+re.count)*Se)),me!==null?(Oe=Math.max(Oe,0),$e=Math.min($e,me.count)):be!=null&&(Oe=Math.max(Oe,0),$e=Math.min($e,be.count));let rt=$e-Oe;if(rt<0||rt===1/0)return;de.setup(U,N,le,O,me);let at,Qe=R;if(me!==null&&(at=G.get(me),Qe=ce,Qe.setIndex(at)),U.isMesh)N.wireframe===!0?(ve.setLineWidth(N.wireframeLinewidth*lt()),Qe.setMode(C.LINES)):Qe.setMode(C.TRIANGLES);else if(U.isLine){let Ae=N.linewidth;Ae===void 0&&(Ae=1),ve.setLineWidth(Ae*lt()),U.isLineSegments?Qe.setMode(C.LINES):U.isLineLoop?Qe.setMode(C.LINE_LOOP):Qe.setMode(C.LINE_STRIP)}else U.isPoints?Qe.setMode(C.POINTS):U.isSprite&&Qe.setMode(C.TRIANGLES);if(U.isBatchedMesh)if(U._multiDrawInstances!==null)yi("WebGLRenderer: renderMultiDrawInstances has been deprecated and will be removed in r184. Append to renderMultiDraw arguments and use indirection."),Qe.renderMultiDrawInstances(U._multiDrawStarts,U._multiDrawCounts,U._multiDrawCount,U._multiDrawInstances);else if(We.get("WEBGL_multi_draw"))Qe.renderMultiDraw(U._multiDrawStarts,U._multiDrawCounts,U._multiDrawCount);else{let Ae=U._multiDrawStarts,Ze=U._multiDrawCounts,Ge=U._multiDrawCount,It=me?G.get(me).bytesPerElement:1,ri=g.get(N).currentProgram.getUniforms();for(let Pt=0;Pt<Ge;Pt++)ri.setValue(C,"_gl_DrawID",Pt),Qe.render(Ae[Pt]/It,Ze[Pt])}else if(U.isInstancedMesh)Qe.renderInstances(Oe,rt,U.count);else if(O.isInstancedBufferGeometry){let Ae=O._maxInstanceCount!==void 0?O._maxInstanceCount:1/0,Ze=Math.min(O.instanceCount,Ae);Qe.renderInstances(Oe,rt,Ze)}else Qe.render(Oe,rt)};function wo(x,D,O){x.transparent===!0&&x.side===rn&&x.forceSinglePass===!1?(x.side=Tt,x.needsUpdate=!0,ds(x,D,O),x.side=xn,x.needsUpdate=!0,ds(x,D,O),x.side=rn):ds(x,D,O)}this.compile=function(x,D,O=null){O===null&&(O=x),E=se.get(O),E.init(D),I.push(E),O.traverseVisible(function(U){U.isLight&&U.layers.test(D.layers)&&(E.pushLight(U),U.castShadow&&E.pushShadow(U))}),x!==O&&x.traverseVisible(function(U){U.isLight&&U.layers.test(D.layers)&&(E.pushLight(U),U.castShadow&&E.pushShadow(U))}),E.setupLights();let N=new Set;return x.traverse(function(U){if(!(U.isMesh||U.isPoints||U.isLine||U.isSprite))return;let re=U.material;if(re)if(Array.isArray(re))for(let fe=0;fe<re.length;fe++){let le=re[fe];wo(le,O,U),N.add(le)}else wo(re,O,U),N.add(re)}),E=I.pop(),N},this.compileAsync=function(x,D,O=null){let N=this.compile(x,D,O);return new Promise(U=>{function re(){if(N.forEach(function(fe){g.get(fe).currentProgram.isReady()&&N.delete(fe)}),N.size===0){U(x);return}setTimeout(re,10)}We.get("KHR_parallel_shader_compile")!==null?re():setTimeout(re,10)})};let aa=null;function hc(x){aa&&aa(x)}function Co(){zn.stop()}function Ro(){zn.start()}let zn=new sc;zn.setAnimationLoop(hc),typeof self<"u"&&zn.setContext(self),this.setAnimationLoop=function(x){aa=x,te.setAnimationLoop(x),x===null?zn.stop():zn.start()},te.addEventListener("sessionstart",Co),te.addEventListener("sessionend",Ro),this.render=function(x,D){if(D!==void 0&&D.isCamera!==!0){Ee("WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(M===!0)return;let O=te.enabled===!0&&te.isPresenting===!0,N=B!==null&&(z===null||O)&&B.begin(v,z);if(x.matrixWorldAutoUpdate===!0&&x.updateMatrixWorld(),D.parent===null&&D.matrixWorldAutoUpdate===!0&&D.updateMatrixWorld(),te.enabled===!0&&te.isPresenting===!0&&(B===null||B.isCompositing()===!1)&&(te.cameraAutoUpdate===!0&&te.updateCamera(D),D=te.getCamera()),x.isScene===!0&&x.onBeforeRender(v,x,D,z),E=se.get(x,I.length),E.init(D),I.push(E),pt.multiplyMatrices(D.projectionMatrix,D.matrixWorldInverse),Pe.setFromProjectionMatrix(pt,Zt,D.reversedDepth),ke=this.localClippingEnabled,_e=ge.init(this.clippingPlanes,ke),A=j.get(x,w.length),A.init(),w.push(A),te.enabled===!0&&te.isPresenting===!0){let fe=v.xr.getDepthSensingMesh();fe!==null&&oa(fe,D,-1/0,v.sortObjects)}oa(x,D,0,v.sortObjects),A.finish(),v.sortObjects===!0&&A.sort(st,nt),Ue=te.enabled===!1||te.isPresenting===!1||te.hasDepthSensing()===!1,Ue&&ie.addToRenderList(A,x),this.info.render.frame++,_e===!0&&ge.beginShadows();let U=E.state.shadowsArray;if(ye.render(U,x,D),_e===!0&&ge.endShadows(),this.info.autoReset===!0&&this.info.reset(),(N&&B.hasRenderPass())===!1){let fe=A.opaque,le=A.transmissive;if(E.setupLights(),D.isArrayCamera){let me=D.cameras;if(le.length>0)for(let Se=0,Te=me.length;Se<Te;Se++){let be=me[Se];Po(fe,le,x,be)}Ue&&ie.render(x);for(let Se=0,Te=me.length;Se<Te;Se++){let be=me[Se];Io(A,x,be,be.viewport)}}else le.length>0&&Po(fe,le,x,D),Ue&&ie.render(x),Io(A,x,D)}z!==null&&V===0&&(P.updateMultisampleRenderTarget(z),P.updateRenderTargetMipmap(z)),N&&B.end(v),x.isScene===!0&&x.onAfterRender(v,x,D),de.resetDefaultState(),W=-1,Y=null,I.pop(),I.length>0?(E=I[I.length-1],_e===!0&&ge.setGlobalState(v.clippingPlanes,E.state.camera)):E=null,w.pop(),w.length>0?A=w[w.length-1]:A=null};function oa(x,D,O,N){if(x.visible===!1)return;if(x.layers.test(D.layers)){if(x.isGroup)O=x.renderOrder;else if(x.isLOD)x.autoUpdate===!0&&x.update(D);else if(x.isLight)E.pushLight(x),x.castShadow&&E.pushShadow(x);else if(x.isSprite){if(!x.frustumCulled||Pe.intersectsSprite(x)){N&&qe.setFromMatrixPosition(x.matrixWorld).applyMatrix4(pt);let fe=ne.update(x),le=x.material;le.visible&&A.push(x,fe,le,O,qe.z,null)}}else if((x.isMesh||x.isLine||x.isPoints)&&(!x.frustumCulled||Pe.intersectsObject(x))){let fe=ne.update(x),le=x.material;if(N&&(x.boundingSphere!==void 0?(x.boundingSphere===null&&x.computeBoundingSphere(),qe.copy(x.boundingSphere.center)):(fe.boundingSphere===null&&fe.computeBoundingSphere(),qe.copy(fe.boundingSphere.center)),qe.applyMatrix4(x.matrixWorld).applyMatrix4(pt)),Array.isArray(le)){let me=fe.groups;for(let Se=0,Te=me.length;Se<Te;Se++){let be=me[Se],Oe=le[be.materialIndex];Oe&&Oe.visible&&A.push(x,fe,Oe,O,qe.z,be)}}else le.visible&&A.push(x,fe,le,O,qe.z,null)}}let re=x.children;for(let fe=0,le=re.length;fe<le;fe++)oa(re[fe],D,O,N)}function Io(x,D,O,N){let{opaque:U,transmissive:re,transparent:fe}=x;E.setupLightsView(O),_e===!0&&ge.setGlobalState(v.clippingPlanes,O),N&&ve.viewport(k.copy(N)),U.length>0&&us(U,D,O),re.length>0&&us(re,D,O),fe.length>0&&us(fe,D,O),ve.buffers.depth.setTest(!0),ve.buffers.depth.setMask(!0),ve.buffers.color.setMask(!0),ve.setPolygonOffset(!1)}function Po(x,D,O,N){if((O.isScene===!0?O.overrideMaterial:null)!==null)return;if(E.state.transmissionRenderTarget[N.id]===void 0){let Oe=We.has("EXT_color_buffer_half_float")||We.has("EXT_color_buffer_float");E.state.transmissionRenderTarget[N.id]=new Nt(1,1,{generateMipmaps:!0,type:Oe?on:Bt,minFilter:Fn,samples:je.samples,stencilBuffer:r,resolveDepthBuffer:!1,resolveStencilBuffer:!1,colorSpace:ze.workingColorSpace})}let re=E.state.transmissionRenderTarget[N.id],fe=N.viewport||k;re.setSize(fe.z*v.transmissionResolutionScale,fe.w*v.transmissionResolutionScale);let le=v.getRenderTarget(),me=v.getActiveCubeFace(),Se=v.getActiveMipmapLevel();v.setRenderTarget(re),v.getClearColor(he),ae=v.getClearAlpha(),ae<1&&v.setClearColor(16777215,.5),v.clear(),Ue&&ie.render(O);let Te=v.toneMapping;v.toneMapping=Jt;let be=N.viewport;if(N.viewport!==void 0&&(N.viewport=void 0),E.setupLightsView(N),_e===!0&&ge.setGlobalState(v.clippingPlanes,N),us(x,O,N),P.updateMultisampleRenderTarget(re),P.updateRenderTargetMipmap(re),We.has("WEBGL_multisampled_render_to_texture")===!1){let Oe=!1;for(let $e=0,rt=D.length;$e<rt;$e++){let at=D[$e],{object:Qe,geometry:Ae,material:Ze,group:Ge}=at;if(Ze.side===rn&&Qe.layers.test(N.layers)){let It=Ze.side;Ze.side=Tt,Ze.needsUpdate=!0,Lo(Qe,O,N,Ae,Ze,Ge),Ze.side=It,Ze.needsUpdate=!0,Oe=!0}}Oe===!0&&(P.updateMultisampleRenderTarget(re),P.updateRenderTargetMipmap(re))}v.setRenderTarget(le,me,Se),v.setClearColor(he,ae),be!==void 0&&(N.viewport=be),v.toneMapping=Te}function us(x,D,O){let N=D.isScene===!0?D.overrideMaterial:null;for(let U=0,re=x.length;U<re;U++){let fe=x[U],{object:le,geometry:me,group:Se}=fe,Te=fe.material;Te.allowOverride===!0&&N!==null&&(Te=N),le.layers.test(O.layers)&&Lo(le,D,O,me,Te,Se)}}function Lo(x,D,O,N,U,re){x.onBeforeRender(v,D,O,N,U,re),x.modelViewMatrix.multiplyMatrices(O.matrixWorldInverse,x.matrixWorld),x.normalMatrix.getNormalMatrix(x.modelViewMatrix),U.onBeforeRender(v,D,O,N,x,re),U.transparent===!0&&U.side===rn&&U.forceSinglePass===!1?(U.side=Tt,U.needsUpdate=!0,v.renderBufferDirect(O,D,N,U,x,re),U.side=xn,U.needsUpdate=!0,v.renderBufferDirect(O,D,N,U,x,re),U.side=rn):v.renderBufferDirect(O,D,N,U,x,re),x.onAfterRender(v,D,O,N,U,re)}function ds(x,D,O){D.isScene!==!0&&(D=Ke);let N=g.get(x),U=E.state.lights,re=E.state.shadowsArray,fe=U.state.version,le=xe.getParameters(x,U.state,re,D,O),me=xe.getProgramCacheKey(le),Se=N.programs;N.environment=x.isMeshStandardMaterial?D.environment:null,N.fog=D.fog,N.envMap=(x.isMeshStandardMaterial?J:X).get(x.envMap||N.environment),N.envMapRotation=N.environment!==null&&x.envMap===null?D.environmentRotation:x.envMapRotation,Se===void 0&&(x.addEventListener("dispose",Qt),Se=new Map,N.programs=Se);let Te=Se.get(me);if(Te!==void 0){if(N.currentProgram===Te&&N.lightsStateVersion===fe)return Uo(x,le),Te}else le.uniforms=xe.getUniforms(x),x.onBeforeCompile(le,v),Te=xe.acquireProgram(le,me),Se.set(me,Te),N.uniforms=le.uniforms;let be=N.uniforms;return(!x.isShaderMaterial&&!x.isRawShaderMaterial||x.clipping===!0)&&(be.clippingPlanes=ge.uniform),Uo(x,le),N.needsLights=fc(x),N.lightsStateVersion=fe,N.needsLights&&(be.ambientLightColor.value=U.state.ambient,be.lightProbe.value=U.state.probe,be.directionalLights.value=U.state.directional,be.directionalLightShadows.value=U.state.directionalShadow,be.spotLights.value=U.state.spot,be.spotLightShadows.value=U.state.spotShadow,be.rectAreaLights.value=U.state.rectArea,be.ltc_1.value=U.state.rectAreaLTC1,be.ltc_2.value=U.state.rectAreaLTC2,be.pointLights.value=U.state.point,be.pointLightShadows.value=U.state.pointShadow,be.hemisphereLights.value=U.state.hemi,be.directionalShadowMap.value=U.state.directionalShadowMap,be.directionalShadowMatrix.value=U.state.directionalShadowMatrix,be.spotShadowMap.value=U.state.spotShadowMap,be.spotLightMatrix.value=U.state.spotLightMatrix,be.spotLightMap.value=U.state.spotLightMap,be.pointShadowMap.value=U.state.pointShadowMap,be.pointShadowMatrix.value=U.state.pointShadowMatrix),N.currentProgram=Te,N.uniformsList=null,Te}function Do(x){if(x.uniformsList===null){let D=x.currentProgram.getUniforms();x.uniformsList=Ri.seqWithValue(D.seq,x.uniforms)}return x.uniformsList}function Uo(x,D){let O=g.get(x);O.outputColorSpace=D.outputColorSpace,O.batching=D.batching,O.batchingColor=D.batchingColor,O.instancing=D.instancing,O.instancingColor=D.instancingColor,O.instancingMorph=D.instancingMorph,O.skinning=D.skinning,O.morphTargets=D.morphTargets,O.morphNormals=D.morphNormals,O.morphColors=D.morphColors,O.morphTargetsCount=D.morphTargetsCount,O.numClippingPlanes=D.numClippingPlanes,O.numIntersection=D.numClipIntersection,O.vertexAlphas=D.vertexAlphas,O.vertexTangents=D.vertexTangents,O.toneMapping=D.toneMapping}function uc(x,D,O,N,U){D.isScene!==!0&&(D=Ke),P.resetTextureUnits();let re=D.fog,fe=N.isMeshStandardMaterial?D.environment:null,le=z===null?v.outputColorSpace:z.isXRRenderTarget===!0?z.texture.colorSpace:Zn,me=(N.isMeshStandardMaterial?J:X).get(N.envMap||fe),Se=N.vertexColors===!0&&!!O.attributes.color&&O.attributes.color.itemSize===4,Te=!!O.attributes.tangent&&(!!N.normalMap||N.anisotropy>0),be=!!O.morphAttributes.position,Oe=!!O.morphAttributes.normal,$e=!!O.morphAttributes.color,rt=Jt;N.toneMapped&&(z===null||z.isXRRenderTarget===!0)&&(rt=v.toneMapping);let at=O.morphAttributes.position||O.morphAttributes.normal||O.morphAttributes.color,Qe=at!==void 0?at.length:0,Ae=g.get(N),Ze=E.state.lights;if(_e===!0&&(ke===!0||x!==Y)){let St=x===Y&&N.id===W;ge.setState(N,x,St)}let Ge=!1;N.version===Ae.__version?(Ae.needsLights&&Ae.lightsStateVersion!==Ze.state.version||Ae.outputColorSpace!==le||U.isBatchedMesh&&Ae.batching===!1||!U.isBatchedMesh&&Ae.batching===!0||U.isBatchedMesh&&Ae.batchingColor===!0&&U.colorTexture===null||U.isBatchedMesh&&Ae.batchingColor===!1&&U.colorTexture!==null||U.isInstancedMesh&&Ae.instancing===!1||!U.isInstancedMesh&&Ae.instancing===!0||U.isSkinnedMesh&&Ae.skinning===!1||!U.isSkinnedMesh&&Ae.skinning===!0||U.isInstancedMesh&&Ae.instancingColor===!0&&U.instanceColor===null||U.isInstancedMesh&&Ae.instancingColor===!1&&U.instanceColor!==null||U.isInstancedMesh&&Ae.instancingMorph===!0&&U.morphTexture===null||U.isInstancedMesh&&Ae.instancingMorph===!1&&U.morphTexture!==null||Ae.envMap!==me||N.fog===!0&&Ae.fog!==re||Ae.numClippingPlanes!==void 0&&(Ae.numClippingPlanes!==ge.numPlanes||Ae.numIntersection!==ge.numIntersection)||Ae.vertexAlphas!==Se||Ae.vertexTangents!==Te||Ae.morphTargets!==be||Ae.morphNormals!==Oe||Ae.morphColors!==$e||Ae.toneMapping!==rt||Ae.morphTargetsCount!==Qe)&&(Ge=!0):(Ge=!0,Ae.__version=N.version);let It=Ae.currentProgram;Ge===!0&&(It=ds(N,D,U));let ri=!1,Pt=!1,Pi=!1,tt=It.getUniforms(),Et=Ae.uniforms;if(ve.useProgram(It.program)&&(ri=!0,Pt=!0,Pi=!0),N.id!==W&&(W=N.id,Pt=!0),ri||Y!==x){ve.buffers.depth.getReversed()&&x.reversedDepth!==!0&&(x._reversedDepth=!0,x.updateProjectionMatrix()),tt.setValue(C,"projectionMatrix",x.projectionMatrix),tt.setValue(C,"viewMatrix",x.matrixWorldInverse);let wt=tt.map.cameraPosition;wt!==void 0&&wt.setValue(C,Ve.setFromMatrixPosition(x.matrixWorld)),je.logarithmicDepthBuffer&&tt.setValue(C,"logDepthBufFC",2/(Math.log(x.far+1)/Math.LN2)),(N.isMeshPhongMaterial||N.isMeshToonMaterial||N.isMeshLambertMaterial||N.isMeshBasicMaterial||N.isMeshStandardMaterial||N.isShaderMaterial)&&tt.setValue(C,"isOrthographic",x.isOrthographicCamera===!0),Y!==x&&(Y=x,Pt=!0,Pi=!0)}if(Ae.needsLights&&(Ze.state.directionalShadowMap.length>0&&tt.setValue(C,"directionalShadowMap",Ze.state.directionalShadowMap,P),Ze.state.spotShadowMap.length>0&&tt.setValue(C,"spotShadowMap",Ze.state.spotShadowMap,P),Ze.state.pointShadowMap.length>0&&tt.setValue(C,"pointShadowMap",Ze.state.pointShadowMap,P)),U.isSkinnedMesh){tt.setOptional(C,U,"bindMatrix"),tt.setOptional(C,U,"bindMatrixInverse");let St=U.skeleton;St&&(St.boneTexture===null&&St.computeBoneTexture(),tt.setValue(C,"boneTexture",St.boneTexture,P))}U.isBatchedMesh&&(tt.setOptional(C,U,"batchingTexture"),tt.setValue(C,"batchingTexture",U._matricesTexture,P),tt.setOptional(C,U,"batchingIdTexture"),tt.setValue(C,"batchingIdTexture",U._indirectTexture,P),tt.setOptional(C,U,"batchingColorTexture"),U._colorsTexture!==null&&tt.setValue(C,"batchingColorTexture",U._colorsTexture,P));let zt=O.morphAttributes;if((zt.position!==void 0||zt.normal!==void 0||zt.color!==void 0)&&Ne.update(U,O,It),(Pt||Ae.receiveShadow!==U.receiveShadow)&&(Ae.receiveShadow=U.receiveShadow,tt.setValue(C,"receiveShadow",U.receiveShadow)),N.isMeshGouraudMaterial&&N.envMap!==null&&(Et.envMap.value=me,Et.flipEnvMap.value=me.isCubeTexture&&me.isRenderTargetTexture===!1?-1:1),N.isMeshStandardMaterial&&N.envMap===null&&D.environment!==null&&(Et.envMapIntensity.value=D.environmentIntensity),Et.dfgLUT!==void 0&&(Et.dfgLUT.value=Op()),Pt&&(tt.setValue(C,"toneMappingExposure",v.toneMappingExposure),Ae.needsLights&&dc(Et,Pi),re&&N.fog===!0&&we.refreshFogUniforms(Et,re),we.refreshMaterialUniforms(Et,N,De,Fe,E.state.transmissionRenderTarget[x.id]),Ri.upload(C,Do(Ae),Et,P)),N.isShaderMaterial&&N.uniformsNeedUpdate===!0&&(Ri.upload(C,Do(Ae),Et,P),N.uniformsNeedUpdate=!1),N.isSpriteMaterial&&tt.setValue(C,"center",U.center),tt.setValue(C,"modelViewMatrix",U.modelViewMatrix),tt.setValue(C,"normalMatrix",U.normalMatrix),tt.setValue(C,"modelMatrix",U.matrixWorld),N.isShaderMaterial||N.isRawShaderMaterial){let St=N.uniformsGroups;for(let wt=0,la=St.length;wt<la;wt++){let Vn=St[wt];Q.update(Vn,It),Q.bind(Vn,It)}}return It}function dc(x,D){x.ambientLightColor.needsUpdate=D,x.lightProbe.needsUpdate=D,x.directionalLights.needsUpdate=D,x.directionalLightShadows.needsUpdate=D,x.pointLights.needsUpdate=D,x.pointLightShadows.needsUpdate=D,x.spotLights.needsUpdate=D,x.spotLightShadows.needsUpdate=D,x.rectAreaLights.needsUpdate=D,x.hemisphereLights.needsUpdate=D}function fc(x){return x.isMeshLambertMaterial||x.isMeshToonMaterial||x.isMeshPhongMaterial||x.isMeshStandardMaterial||x.isShadowMaterial||x.isShaderMaterial&&x.lights===!0}this.getActiveCubeFace=function(){return L},this.getActiveMipmapLevel=function(){return V},this.getRenderTarget=function(){return z},this.setRenderTargetTextures=function(x,D,O){let N=g.get(x);N.__autoAllocateDepthBuffer=x.resolveDepthBuffer===!1,N.__autoAllocateDepthBuffer===!1&&(N.__useRenderToTexture=!1),g.get(x.texture).__webglTexture=D,g.get(x.depthTexture).__webglTexture=N.__autoAllocateDepthBuffer?void 0:O,N.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(x,D){let O=g.get(x);O.__webglFramebuffer=D,O.__useDefaultFramebuffer=D===void 0};let pc=C.createFramebuffer();this.setRenderTarget=function(x,D=0,O=0){z=x,L=D,V=O;let N=null,U=!1,re=!1;if(x){let le=g.get(x);if(le.__useDefaultFramebuffer!==void 0){ve.bindFramebuffer(C.FRAMEBUFFER,le.__webglFramebuffer),k.copy(x.viewport),H.copy(x.scissor),$=x.scissorTest,ve.viewport(k),ve.scissor(H),ve.setScissorTest($),W=-1;return}else if(le.__webglFramebuffer===void 0)P.setupRenderTarget(x);else if(le.__hasExternalTextures)P.rebindTextures(x,g.get(x.texture).__webglTexture,g.get(x.depthTexture).__webglTexture);else if(x.depthBuffer){let Te=x.depthTexture;if(le.__boundDepthTexture!==Te){if(Te!==null&&g.has(Te)&&(x.width!==Te.image.width||x.height!==Te.image.height))throw new Error("WebGLRenderTarget: Attached DepthTexture is initialized to the incorrect size.");P.setupDepthRenderbuffer(x)}}let me=x.texture;(me.isData3DTexture||me.isDataArrayTexture||me.isCompressedArrayTexture)&&(re=!0);let Se=g.get(x).__webglFramebuffer;x.isWebGLCubeRenderTarget?(Array.isArray(Se[D])?N=Se[D][O]:N=Se[D],U=!0):x.samples>0&&P.useMultisampledRTT(x)===!1?N=g.get(x).__webglMultisampledFramebuffer:Array.isArray(Se)?N=Se[O]:N=Se,k.copy(x.viewport),H.copy(x.scissor),$=x.scissorTest}else k.copy(q).multiplyScalar(De).floor(),H.copy(K).multiplyScalar(De).floor(),$=pe;if(O!==0&&(N=pc),ve.bindFramebuffer(C.FRAMEBUFFER,N)&&ve.drawBuffers(x,N),ve.viewport(k),ve.scissor(H),ve.setScissorTest($),U){let le=g.get(x.texture);C.framebufferTexture2D(C.FRAMEBUFFER,C.COLOR_ATTACHMENT0,C.TEXTURE_CUBE_MAP_POSITIVE_X+D,le.__webglTexture,O)}else if(re){let le=D;for(let me=0;me<x.textures.length;me++){let Se=g.get(x.textures[me]);C.framebufferTextureLayer(C.FRAMEBUFFER,C.COLOR_ATTACHMENT0+me,Se.__webglTexture,O,le)}}else if(x!==null&&O!==0){let le=g.get(x.texture);C.framebufferTexture2D(C.FRAMEBUFFER,C.COLOR_ATTACHMENT0,C.TEXTURE_2D,le.__webglTexture,O)}W=-1},this.readRenderTargetPixels=function(x,D,O,N,U,re,fe,le=0){if(!(x&&x.isWebGLRenderTarget)){Ee("WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let me=g.get(x).__webglFramebuffer;if(x.isWebGLCubeRenderTarget&&fe!==void 0&&(me=me[fe]),me){ve.bindFramebuffer(C.FRAMEBUFFER,me);try{let Se=x.textures[le],Te=Se.format,be=Se.type;if(!je.textureFormatReadable(Te)){Ee("WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(!je.textureTypeReadable(be)){Ee("WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}D>=0&&D<=x.width-N&&O>=0&&O<=x.height-U&&(x.textures.length>1&&C.readBuffer(C.COLOR_ATTACHMENT0+le),C.readPixels(D,O,N,U,ee.convert(Te),ee.convert(be),re))}finally{let Se=z!==null?g.get(z).__webglFramebuffer:null;ve.bindFramebuffer(C.FRAMEBUFFER,Se)}}},this.readRenderTargetPixelsAsync=async function(x,D,O,N,U,re,fe,le=0){if(!(x&&x.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let me=g.get(x).__webglFramebuffer;if(x.isWebGLCubeRenderTarget&&fe!==void 0&&(me=me[fe]),me)if(D>=0&&D<=x.width-N&&O>=0&&O<=x.height-U){ve.bindFramebuffer(C.FRAMEBUFFER,me);let Se=x.textures[le],Te=Se.format,be=Se.type;if(!je.textureFormatReadable(Te))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(!je.textureTypeReadable(be))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");let Oe=C.createBuffer();C.bindBuffer(C.PIXEL_PACK_BUFFER,Oe),C.bufferData(C.PIXEL_PACK_BUFFER,re.byteLength,C.STREAM_READ),x.textures.length>1&&C.readBuffer(C.COLOR_ATTACHMENT0+le),C.readPixels(D,O,N,U,ee.convert(Te),ee.convert(be),0);let $e=z!==null?g.get(z).__webglFramebuffer:null;ve.bindFramebuffer(C.FRAMEBUFFER,$e);let rt=C.fenceSync(C.SYNC_GPU_COMMANDS_COMPLETE,0);return C.flush(),await Ll(C,rt,4),C.bindBuffer(C.PIXEL_PACK_BUFFER,Oe),C.getBufferSubData(C.PIXEL_PACK_BUFFER,0,re),C.deleteBuffer(Oe),C.deleteSync(rt),re}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(x,D=null,O=0){let N=Math.pow(2,-O),U=Math.floor(x.image.width*N),re=Math.floor(x.image.height*N),fe=D!==null?D.x:0,le=D!==null?D.y:0;P.setTexture2D(x,0),C.copyTexSubImage2D(C.TEXTURE_2D,O,0,0,fe,le,U,re),ve.unbindTexture()};let mc=C.createFramebuffer(),gc=C.createFramebuffer();this.copyTextureToTexture=function(x,D,O=null,N=null,U=0,re=null){re===null&&(U!==0?(yi("WebGLRenderer: copyTextureToTexture function signature has changed to support src and dst mipmap levels."),re=U,U=0):re=0);let fe,le,me,Se,Te,be,Oe,$e,rt,at=x.isCompressedTexture?x.mipmaps[re]:x.image;if(O!==null)fe=O.max.x-O.min.x,le=O.max.y-O.min.y,me=O.isBox3?O.max.z-O.min.z:1,Se=O.min.x,Te=O.min.y,be=O.isBox3?O.min.z:0;else{let zt=Math.pow(2,-U);fe=Math.floor(at.width*zt),le=Math.floor(at.height*zt),x.isDataArrayTexture?me=at.depth:x.isData3DTexture?me=Math.floor(at.depth*zt):me=1,Se=0,Te=0,be=0}N!==null?(Oe=N.x,$e=N.y,rt=N.z):(Oe=0,$e=0,rt=0);let Qe=ee.convert(D.format),Ae=ee.convert(D.type),Ze;D.isData3DTexture?(P.setTexture3D(D,0),Ze=C.TEXTURE_3D):D.isDataArrayTexture||D.isCompressedArrayTexture?(P.setTexture2DArray(D,0),Ze=C.TEXTURE_2D_ARRAY):(P.setTexture2D(D,0),Ze=C.TEXTURE_2D),C.pixelStorei(C.UNPACK_FLIP_Y_WEBGL,D.flipY),C.pixelStorei(C.UNPACK_PREMULTIPLY_ALPHA_WEBGL,D.premultiplyAlpha),C.pixelStorei(C.UNPACK_ALIGNMENT,D.unpackAlignment);let Ge=C.getParameter(C.UNPACK_ROW_LENGTH),It=C.getParameter(C.UNPACK_IMAGE_HEIGHT),ri=C.getParameter(C.UNPACK_SKIP_PIXELS),Pt=C.getParameter(C.UNPACK_SKIP_ROWS),Pi=C.getParameter(C.UNPACK_SKIP_IMAGES);C.pixelStorei(C.UNPACK_ROW_LENGTH,at.width),C.pixelStorei(C.UNPACK_IMAGE_HEIGHT,at.height),C.pixelStorei(C.UNPACK_SKIP_PIXELS,Se),C.pixelStorei(C.UNPACK_SKIP_ROWS,Te),C.pixelStorei(C.UNPACK_SKIP_IMAGES,be);let tt=x.isDataArrayTexture||x.isData3DTexture,Et=D.isDataArrayTexture||D.isData3DTexture;if(x.isDepthTexture){let zt=g.get(x),St=g.get(D),wt=g.get(zt.__renderTarget),la=g.get(St.__renderTarget);ve.bindFramebuffer(C.READ_FRAMEBUFFER,wt.__webglFramebuffer),ve.bindFramebuffer(C.DRAW_FRAMEBUFFER,la.__webglFramebuffer);for(let Vn=0;Vn<me;Vn++)tt&&(C.framebufferTextureLayer(C.READ_FRAMEBUFFER,C.COLOR_ATTACHMENT0,g.get(x).__webglTexture,U,be+Vn),C.framebufferTextureLayer(C.DRAW_FRAMEBUFFER,C.COLOR_ATTACHMENT0,g.get(D).__webglTexture,re,rt+Vn)),C.blitFramebuffer(Se,Te,fe,le,Oe,$e,fe,le,C.DEPTH_BUFFER_BIT,C.NEAREST);ve.bindFramebuffer(C.READ_FRAMEBUFFER,null),ve.bindFramebuffer(C.DRAW_FRAMEBUFFER,null)}else if(U!==0||x.isRenderTargetTexture||g.has(x)){let zt=g.get(x),St=g.get(D);ve.bindFramebuffer(C.READ_FRAMEBUFFER,mc),ve.bindFramebuffer(C.DRAW_FRAMEBUFFER,gc);for(let wt=0;wt<me;wt++)tt?C.framebufferTextureLayer(C.READ_FRAMEBUFFER,C.COLOR_ATTACHMENT0,zt.__webglTexture,U,be+wt):C.framebufferTexture2D(C.READ_FRAMEBUFFER,C.COLOR_ATTACHMENT0,C.TEXTURE_2D,zt.__webglTexture,U),Et?C.framebufferTextureLayer(C.DRAW_FRAMEBUFFER,C.COLOR_ATTACHMENT0,St.__webglTexture,re,rt+wt):C.framebufferTexture2D(C.DRAW_FRAMEBUFFER,C.COLOR_ATTACHMENT0,C.TEXTURE_2D,St.__webglTexture,re),U!==0?C.blitFramebuffer(Se,Te,fe,le,Oe,$e,fe,le,C.COLOR_BUFFER_BIT,C.NEAREST):Et?C.copyTexSubImage3D(Ze,re,Oe,$e,rt+wt,Se,Te,fe,le):C.copyTexSubImage2D(Ze,re,Oe,$e,Se,Te,fe,le);ve.bindFramebuffer(C.READ_FRAMEBUFFER,null),ve.bindFramebuffer(C.DRAW_FRAMEBUFFER,null)}else Et?x.isDataTexture||x.isData3DTexture?C.texSubImage3D(Ze,re,Oe,$e,rt,fe,le,me,Qe,Ae,at.data):D.isCompressedArrayTexture?C.compressedTexSubImage3D(Ze,re,Oe,$e,rt,fe,le,me,Qe,at.data):C.texSubImage3D(Ze,re,Oe,$e,rt,fe,le,me,Qe,Ae,at):x.isDataTexture?C.texSubImage2D(C.TEXTURE_2D,re,Oe,$e,fe,le,Qe,Ae,at.data):x.isCompressedTexture?C.compressedTexSubImage2D(C.TEXTURE_2D,re,Oe,$e,at.width,at.height,Qe,at.data):C.texSubImage2D(C.TEXTURE_2D,re,Oe,$e,fe,le,Qe,Ae,at);C.pixelStorei(C.UNPACK_ROW_LENGTH,Ge),C.pixelStorei(C.UNPACK_IMAGE_HEIGHT,It),C.pixelStorei(C.UNPACK_SKIP_PIXELS,ri),C.pixelStorei(C.UNPACK_SKIP_ROWS,Pt),C.pixelStorei(C.UNPACK_SKIP_IMAGES,Pi),re===0&&D.generateMipmaps&&C.generateMipmap(Ze),ve.unbindTexture()},this.initRenderTarget=function(x){g.get(x).__webglFramebuffer===void 0&&P.setupRenderTarget(x)},this.initTexture=function(x){x.isCubeTexture?P.setTextureCube(x,0):x.isData3DTexture?P.setTexture3D(x,0):x.isDataArrayTexture||x.isCompressedArrayTexture?P.setTexture2DArray(x,0):P.setTexture2D(x,0),ve.unbindTexture()},this.resetState=function(){L=0,V=0,z=null,ve.reset(),de.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return Zt}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;let t=this.getContext();t.drawingBufferColorSpace=ze._getDrawingBufferColorSpace(e),t.unpackColorSpace=ze._getUnpackColorSpace()}};var Wt=document.querySelector(".business-visual"),Sn;try{Sn=new ia({alpha:!0,antialias:!0})}catch{}if(Sn){let n=function(d,_,y,m,u=16,b="#344454",T=400){d.font=`${T} ${u}px Inter,Arial`,d.fillStyle=b,d.fillText(_,y,m)},s=function(d,_,y,m,u,b,T=8){d.fillStyle=b,d.beginPath(),d.roundRect(_,y,m,u,T),d.fill()},r=function(d,_,y,m,u,b){let T=document.createElement("canvas");T.width=d,T.height=_;let A=T.getContext("2d");A.shadowColor="#20334a28",A.shadowBlur=25,A.shadowOffsetY=10,s(A,22,15,d-44,_-43,"#fff",14),A.shadowColor="transparent",b(A,d,_);let E=new $i(T);E.colorSpace=bt,E.anisotropy=Sn.capabilities.getMaxAnisotropy();let w=new Rt(new Kn(d/170,_/170),new $n({map:E,transparent:!0}));return w.position.set(y,m,u),t.add(w),w},p=function(d){requestAnimationFrame(p),!(!h||document.hidden||d-f<33)&&(f=d,!document.body.classList.contains("still")&&!matchMedia("(prefers-reduced-motion:reduce)").matches&&(t.rotation.y+=(l-t.rotation.y)*.04,o.position.y=-.9+Math.sin(d*7e-4)*.03,c.position.y=1.55+Math.sin(d*6e-4)*.03),Sn.render(i,e))};Wt.classList.add("with-three","software-scene"),Wt.prepend(Sn.domElement),Sn.domElement.setAttribute("aria-hidden","true"),Sn.setPixelRatio(Math.min(devicePixelRatio,2));let i=new Zi,e=new yt(32,1,.1,50);e.position.z=10;let t=new gn;i.add(t),r(800,520,-.1,.05,0,(d,_,y)=>{s(d,23,16,754,42,"#f1f4f6",13);for(let m=0;m<3;m++)d.beginPath(),d.arc(43+m*14,37,4,0,7),d.fillStyle=["#dfaa9e","#e2ce91","#afc9ae"][m],d.fill();n(d,"FlowDocker",108,42,12,"#6f8190",600),n(d,"ESPACE / DOANH NGHI\u1EC6P",570,42,9,"#8e9ca7"),s(d,23,60,120,414,"#f7f9fa",0),n(d,"F /",43,102,22,"#34516d",700),["T\u1ED5ng quan","H\u1ED3 s\u01A1","C\xF4ng vi\u1EC7c","Quy tr\xECnh"].forEach((m,u)=>{u===1&&s(d,33,154,100,30,"#e1eaf1",5),n(d,m,44,143+u*32,11,u===1?"#365978":"#97a3ad")}),n(d,"H\u1ED3 s\u01A1 c\u1EE7a doanh nghi\u1EC7p",168,105,24,"#273c50",600),n(d,"Theo d\xF5i c\xF4ng vi\u1EC7c qua t\u1EEBng b\u01B0\u1EDBc x\u1EED l\xFD.",168,134,11,"#9ca7af"),s(d,655,85,95,30,"#2b455e",6),n(d,"+ T\u1EA1o h\u1ED3 s\u01A1",666,104,10,"#fff"),n(d,"T\u1EA5t c\u1EA3 h\u1ED3 s\u01A1",170,177,11,"#3e5a72",500),n(d,"Ch\u1EDD ph\xEA duy\u1EC7t",300,177,11,"#98a4ae"),s(d,165,193,580,1,"#e6ebef",0),["\u0110\u1EC1 ngh\u1ECB mua s\u1EAFm thi\u1EBFt b\u1ECB","H\u1EE3p \u0111\u1ED3ng d\u1ECBch v\u1EE5","\u0110\u1EC1 ngh\u1ECB thanh to\xE1n"].forEach((m,u)=>{let b=244+u*65;s(d,175,b,28,35,"#eef2f5",4),n(d,"\u2261",182,b+23,18,"#8da2b2"),n(d,m,218,b+15,13,"#445767",500),n(d,["V\u1EADn h\xE0nh \xB7 DEMO\u2013001","Kinh doanh \xB7 DEMO\u2013002","T\xE0i ch\xEDnh \xB7 DEMO\u2013003"][u],218,b+33,9,"#a4adb4"),s(d,607,b+2,126,25,u===1?"#e7f1e8":"#f4f0e4",13),n(d,u===1?"\u0110\xE3 ho\xE0n t\u1EA5t":"Ch\u1EDD ph\xEA duy\u1EC7t",619,b+18,10,u===1?"#7c9978":"#ab9663"),s(d,172,b+48,568,1,"#eff2f4",0)}),n(d,"GIAO DI\u1EC6N MINH H\u1ECCA",170,458,8,"#a6b0b7")}).rotation.set(.025,-.16,-.02);let o=r(360,320,1.8,-.9,.75,(d,_,y)=>{s(d,22,15,_-44,y-43,"#263e53",14),n(d,"LU\u1ED2NG PH\xCA DUY\u1EC6T",45,50,9,"#9fb4c5"),n(d,"\u0110\u1EC1 ngh\u1ECB mua s\u1EAFm",45,81,18,"#edf4f8",550),["Ng\u01B0\u1EDDi t\u1EA1o h\u1ED3 s\u01A1","Tr\u01B0\u1EDFng b\u1ED9 ph\u1EADn","Ng\u01B0\u1EDDi k\xFD t\xE0i li\u1EC7u"].forEach((m,u)=>{let b=118+u*55;s(d,48,b-9,19,19,u===2?"#6c8294":"#cbdcbc",10),n(d,u===2?"3":"\u2713",53,b+5,10,"#46613c"),n(d,m,85,b+2,12,"#e4edf4"),n(d,u===2?"\u0110ang ch\u1EDD k\xFD":"\u0110\xE3 ho\xE0n t\u1EA5t",85,b+20,9,"#9db2c3")})});o.rotation.z=.025;let c=r(340,120,-1.7,1.55,.9,d=>{s(d,38,34,40,40,"#e7f0e1",12),n(d,"\u2713",49,61,24,"#819d69"),n(d,"H\u1ED3 s\u01A1 \u0111\xE3 ho\xE0n t\u1EA5t",94,49,13,"#40513c",550),n(d,"PDF s\u1EB5n s\xE0ng l\u01B0u tr\u1EEF",94,69,9,"#9da994")});c.rotation.z=.025;let l=0,h=!0,f=0;new ResizeObserver(()=>{Sn.setSize(Wt.clientWidth,Wt.clientHeight),e.aspect=Wt.clientWidth/Wt.clientHeight,e.position.z=Wt.clientWidth<450?13:10,e.updateProjectionMatrix(),Sn.render(i,e)}).observe(Wt),new IntersectionObserver(([d])=>h=d.isIntersecting).observe(Wt),Wt.addEventListener("pointermove",d=>{let _=Wt.getBoundingClientRect();l=((d.clientX-_.left)/_.width-.5)*.13}),Wt.addEventListener("pointerleave",()=>l=0),requestAnimationFrame(p)}
/*! Bundled license information:

three/build/three.core.js:
three/build/three.module.js:
  (**
   * @license
   * Copyright 2010-2025 Three.js Authors
   * SPDX-License-Identifier: MIT
   *)
*/
