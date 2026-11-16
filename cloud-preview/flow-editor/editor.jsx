import React, {useState, useEffect} from 'react';
import {createRoot} from 'react-dom/client';
import {ReactFlow, Background, Controls, Handle, Position, applyNodeChanges, useReactFlow} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './editor.css';

function FlowNode({data, selected}) {
  return <div className={`bee-flow-node ${selected?'is-selected':''}`}>
    {data.kind!=='trigger'&&<Handle type="target" position={Position[data.input||"Left"]}/>}
    <div className="bee-node-label"><span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true"><path d={data.kind==='trigger'?'M13 2L3 14h8l-1 8 11-13h-8z':data.kind==='scope'?'M3 4h18l-7 8v7l-4 2v-9z':'M4 12h16M14 6l6 6-6 6'}/></svg></span>{data.category}<small style={{marginLeft:'auto'}}>{data.number}</small></div>
    <strong>{data.title}</strong><p>{data.detail}</p>
    <div className="bee-node-foot">{data.kind==='action'?'Action tuần tự':'Bấm để cấu hình'}<span>↗</span></div>
    <Handle type="source" position={Position[data.output||"Right"]}/>
  </div>;
}
const nodeTypes={bee:FlowNode};
function ResizeFit(){const flow=useReactFlow();useEffect(()=>{const element=document.getElementById('bee-flow-canvas');let width=element.clientWidth;let frame;const observer=new ResizeObserver(()=>{const next=element.clientWidth;if(Math.abs(next-width)>40){width=next;cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>flow.fitView({padding:.16,maxZoom:1}));}});observer.observe(element);return()=>{observer.disconnect();cancelAnimationFrame(frame)}},[flow]);return null}
function LayoutButton({reset}) {const flow=useReactFlow();return <button type="button" className="btn" onClick={()=>{reset();requestAnimationFrame(()=>flow.fitView({padding:.16,duration:180}));}}>Sắp xếp lại</button>}
function Editor({model}) {
  const [nodes,setNodes]=useState(model.nodes);
  const [theme,setTheme]=useState(document.documentElement.dataset.theme||'dark');
  useEffect(()=>{const update=e=>setTheme(e.detail);document.addEventListener('beesky:theme',update);return()=>document.removeEventListener('beesky:theme',update)},[]);
  const light=theme==='light';
  const reset=()=>{const next=nodes.map((n,i)=>({...n,position:{x:(Math.floor(i/2)%2?1-i%2:i%2)*330+30,y:Math.floor(i/2)*220+65}}));setNodes(next);window.beeFlowBridge.positions(next)};
  const edges=nodes.slice(1).map((n,i)=>({id:`edge-${i}`,source:nodes[i].id,target:n.id,type:'smoothstep',label:i===0?'Đạt điều kiện':i===1?'Máy phù hợp':'Bước tiếp theo',markerEnd:{type:'arrowclosed',color:light?'#66758b':'#8c99ae'},style:{stroke:light?'#66758b':'#8c99ae',strokeWidth:2},labelStyle:{fill:light?'#5e697a':'#a4abb8',fontSize:11},labelBgStyle:{fill:light?'#f6f7f9':'#101113'},labelBgPadding:[8,5]}));
  return <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} colorMode={theme}
    onNodesChange={changes=>{changes.forEach(c=>{if(c.type==='position'&&c.position)window.beeFlowBridge.position(c.id,c.position)});setNodes(ns=>applyNodeChanges(changes,ns))}}
    onNodeDragStop={(_,node)=>window.beeFlowBridge.position(node.id,node.position)}
    onNodeClick={(_,node)=>window.beeFlowBridge.select(node.id)}
    nodesConnectable={false} edgesReconnectable={false} deleteKeyCode={null}
    onMoveEnd={(_,viewport)=>window.beeFlowBridge.viewport(viewport)} defaultViewport={model.viewport} fitView={!model.viewport} fitViewOptions={{padding:.16,maxZoom:1}} minZoom={.25} maxZoom={1.6}
    proOptions={{hideAttribution:false}} ariaLabelConfig={{'controls.zoomIn.ariaLabel':'Phóng to','controls.zoomOut.ariaLabel':'Thu nhỏ','controls.fitView.ariaLabel':'Vừa khung','controls.interactive.ariaLabel':'Khóa kéo thả'}}>
    <ResizeFit/><Background color={light?'#dce1e8':'#30343b'} gap={22} size={1}/><Controls showInteractive={false}/>
    <div className="bee-canvas-tools"><LayoutButton reset={reset}/><button className="btn primary" type="button" data-ops="action-add">+ Thêm action</button></div>
  </ReactFlow>;
}
let root=null;
window.mountBeeFlow=(element,model)=>{if(root)root.unmount();root=createRoot(element);root.render(<Editor model={model}/>)};
window.unmountBeeFlow=()=>{if(root){root.unmount();root=null}};
