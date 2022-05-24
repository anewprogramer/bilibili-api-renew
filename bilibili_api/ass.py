"""
bilibili_api.ass
有关 ASS 文件的操作
"""
import os
import aiohttp
from bilibili_api.utils.Credential import Credential
from bilibili_api.utils.Danmaku import Danmaku
from bilibili_api.utils.network import get_session
from .utils.danmaku2ass import Danmaku2ASS
from .utils.json2srt import json2srt
from .utils.srt2ass import srt2ass
from .video import Video
from tempfile import gettempdir, tempdir

def export_ass_from_xml(file_local, output_local, stage_size, font_name, font_size, alpha, fly_time, static_time):
    """
    以一个 XML 文件创建 ASS
    一定看清楚 Arguments!
    Args:
        file_local(str)       : 文件输入
        output_local(str)     : 文件输出
        stage_size(tuple(int)): 视频大小
        font_name(str)        : 字体
        font_size(float)      : 字体大小
        alpha(float)          : 透明度(0-1)
        fly_time(float)       : 滚动弹幕持续时间
        static_time(float)    : 静态弹幕持续时间
    """
    Danmaku2ASS(input_files=file_local, input_format="Bilibili", output_file=output_local
                , stage_width=stage_size[0], stage_height=stage_size[1], reserve_blank=0, 
                font_face=font_name, font_size=font_size, text_opacity=alpha, duration_marquee=fly_time,
                duration_still=static_time)

def export_ass_from_srt(file_local, output_local):
    """
    转换 srt 至 ass
    Args:
        file_local(str)  : 文件位置
        output_local(str): 输出位置
    Returns:
        None
    """
    srt2ass(file_local, output_local, "movie")

def export_ass_from_json(file_local, output_local):
    """
    转换 json 至 ass
    Args:
        file_local(str)  : 文件位置
        output_local(str): 输出位置
    Returns:
        None
    """
    json2srt(file_local, output_local.replace(".ass", ".srt"))
    srt2ass(output_local.replace(".ass", ".srt"), output_local, "movie")
    os.remove(output_local.replace(".ass", ".srt"))

async def make_ass_file_subtitle(bvid, out, name, credential=None):
    """
    生成视频字幕文件
    Args:
        bvid(str)             : 视频 BVID
        out(str)              : 输出位置
        name(str)             : 字幕名，如”中文（自动生成）“,是简介的'subtitle'项的'list'项中的弹幕的'lan_doc'属性。
        credential(Credential): 认证
    Returns:
        None
    """
    v = Video(bvid, credential=credential)
    info = await v.get_info()
    json_files = info['subtitle']['list']
    for subtitle in json_files:
        if subtitle['lan_doc'] == name:
            url = subtitle['subtitle_url']
            async with get_session().request("GET", url) as req:
                file_dir = gettempdir() + "/" + "subtitle.json"
                with open(file_dir, "wb") as f:
                    f.write(await req.content.read())
            export_ass_from_json(file_dir, out)
            return
    raise ValueError("没有找到指定字幕")

async def make_ass_file_danmakus(bvid, page, out, credential=None, date=None, font_name="Simsun", font_size=25.0, alpha=1, fly_time=7, static_time=5):
    """
    生成视频弹幕文件 *★,°*:.☆(￣▽￣)/$:*.°★* 。
    强烈推荐 PotPlayer, 电影与电视全部都是静态的，不能滚动。
    Args:
        bvid(str)             : BVID
        page(int)             : 分 P 号
        out(str)              : 输出文件
        credential(Credential): 认证
        date(datetime.date)   : 获取时间
        font_name(str)        : 字体
        font_size(float)      : 字体大小
        alpha(float)          : 透明度(0-1)
        fly_time(float)       : 滚动弹幕持续时间
        static_time(float)    : 静态弹幕持续时间
    Returns:
        None
    """
    if date:
        credential.raise_for_no_sessdata()
    v = Video(bvid, credential=credential)
    info = await  v.get_info()
    width = info['dimension']['width']
    height = info['dimension']['height']
    stage_size = (width, height)
    danmakus = await v.get_danmakus(page, date=date)
    with open(gettempdir() + "/danmaku_temp.xml", "w+", encoding="utf-8") as file:
        file.write("<i>")
        for d in danmakus:
            file.write(d.to_xml())
        file.write("</i>")
    export_ass_from_xml(gettempdir() + "/danmaku_temp.xml", out, stage_size, font_name, 
    font_size, alpha, fly_time, static_time)