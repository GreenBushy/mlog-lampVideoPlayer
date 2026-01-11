function buildVideoBlocks(minX,minY,maxX, unit) {
    let blocksPath = (((Vars.tree.get("mlog-data-blocks/video-blocks-path.txt").readString())).replace(/(\r\n|\n|\r)/g, ''));
    let numBlocks = Number((Vars.tree.get(blocksPath+"/video_blocks.txt")).readString());
    let firstPartOfPathToVideo = (blocksPath + "/block_");

    let i = 0;
    let y = minY;
    let x = minX;
    while(i<numBlocks){

        Call.constructFinish((Vars.world.tile(x, y)),Blocks.microProcessor, unit, 0, unit.team, null);
        let mlogCode = (Vars.tree.get(firstPartOfPathToVideo + String(i) + ".mlog")).readString();
        
        (Vars.world.build(x, y)).updateCode(mlogCode);
        i++;
        x++;

        if (x>maxX){
            x = minX;
            y++;
        }
    }
}
