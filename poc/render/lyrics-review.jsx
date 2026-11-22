import React from 'react';
import {AbsoluteFill, Audio, Composition, registerRoot, staticFile, useCurrentFrame} from 'remotion';
import {reviewState} from './lyrics-timing.mjs';

export function LyricsReview({sourceStart, sourceEnd, fps, rows, audioFile}) {
  const frame = useCurrentFrame();
  const sourceTime = sourceStart + frame / fps;
  const state = reviewState(rows, sourceTime);
  const fallback = state.row?.mode === 'sentence_fallback';
  const progress = Math.min(1, (sourceTime-sourceStart)/(sourceEnd-sourceStart));
  const clock = value => `${Math.floor(value/60)}:${(value%60).toFixed(1).padStart(4,'0').replace('.',',')}`;
  return <AbsoluteFill style={{fontFamily:'Arial',color:'#f2f5f7',background:
    'radial-gradient(ellipse at 15% 10%, #21434a 0%, transparent 65%), radial-gradient(ellipse at 95% 95%, #34344c 0%, transparent 65%), #091b27'}}>
    <Audio src={staticFile(audioFile)} />
    <div style={{position:'absolute',left:50,top:64,fontSize:18,letterSpacing:3,color:'#8dc7bd'}}>LỜI HÁT • TIẾNG VIỆT</div>
    <div style={{position:'absolute',left:50,top:102,fontSize:32,fontWeight:700}}>Nghe và rà soát</div>
    <div style={{position:'absolute',left:50,top:153,fontSize:20,color:'#adbdc8'}}>Bản nháp • Mốc thời gian chưa được duyệt</div>
    <div style={{position:'absolute',left:50,right:50,top:321,fontSize:24,lineHeight:1.5,color:'#7e939f',textAlign:'center'}}>
      {state.index > 0 ? rows[state.index-1].cue.text : ''}
    </div>
    <div style={{position:'absolute',top:416,left:50,right:50,display:'flex',justifyContent:'center'}}>
      <div style={{fontSize:17,letterSpacing:1,padding:'10px 18px',borderRadius:24,
        background:fallback?'#493b29':'#183e3e',color:fallback?'#edc58c':'#96ded0'}}>
        {state.row ? (fallback?'THEO CÂU • CẦN RÀ SOÁT':'TÔ SÁNG THEO TỪ') : 'NHẠC CHUYỂN ĐOẠN'}
      </div>
    </div>
    <div style={{position:'absolute',left:48,right:48,top:492,height:372,display:'flex',alignItems:'center',justifyContent:'center',
      textAlign:'center',fontSize:43,fontWeight:700,lineHeight:1.7,padding:'18px 8px',borderTop:'1px solid #ffffff14',borderBottom:'1px solid #ffffff14'}}>
      <div>{state.row ? (fallback ? state.row.cue.text : state.row.words.map((word,index)=><React.Fragment key={index}>
        <span style={{display:'inline-block',whiteSpace:'nowrap',color:index===state.activeWord?'#f4c56d':(sourceTime>=word.end?'#f2f5f7':'#a4b7c4'),
          borderBottom:`3px solid ${index===state.activeWord?'#f4c56d':'transparent'}`,paddingBottom:2}}>{word.word}</span>{' '}
      </React.Fragment>)) : <span style={{color:'#78929f',fontSize:29}}>Lắng nghe nhạc…</span>}</div>
    </div>
    <div style={{position:'absolute',left:50,right:50,top:923,fontSize:24,lineHeight:1.5,color:'#7e939f',textAlign:'center'}}>
      {state.row && state.index+1<rows.length ? rows[state.index+1].cue.text : ''}
    </div>
    <div style={{position:'absolute',left:50,right:50,bottom:114,display:'flex',justifyContent:'space-between',fontSize:18,color:'#acc0cb'}}>
      <span>{state.row ? `Câu ${state.row.cue.cue_id}` : 'Chuyển câu'}</span><span>Trong bài gốc: {clock(sourceTime)}</span>
    </div>
    <div style={{position:'absolute',left:50,right:50,bottom:89,height:4,borderRadius:4,background:'#ffffff20'}}>
      <div style={{height:4,width:`${progress*100}%`,borderRadius:4,background:'#96ded0'}} />
    </div>
    <div style={{position:'absolute',left:50,right:50,bottom:42,fontSize:16,color:'#819aa7',textAlign:'center'}}>Đoạn 0:43–1:16,9 • 6 câu theo từ, 1 câu hiển thị cả câu</div>
  </AbsoluteFill>;
}

registerRoot(()=> <Composition id="VietnameseLyricsReview" component={LyricsReview}
  width={720} height={1280} fps={30} durationInFrames={1017}
  defaultProps={{sourceStart:43,sourceEnd:76.9,fps:30,rows:[],audioFile:'review-audio.wav'}} />);
