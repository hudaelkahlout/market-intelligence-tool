"""Streamlit entry point. Run with streamlit run app.py."""
import os
import streamlit as st
from dotenv import load_dotenv
from pipeline import analyze
from market_engine import comparison, review_frame, search_apps, ScraperError
from dashboard import build_charts
from market_ai import generate_insights, SECTIONS
from reporting import build_report

load_dotenv()

def configuration(name, default=None):
    value=os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name,default)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return default

def main():
    st.set_page_config(page_title='Market Intelligence', page_icon='📊', layout='wide')
    st.title('Market Intelligence & Competitor Research')
    st.write('Search Google Play, compare 2–4 competitors, and turn review evidence into opportunities.')
    with st.form('search'):
        query = st.text_input('App name, niche keyword, or category')
        submitted = st.form_submit_button('Search')
    if submitted:
        try:
            with st.spinner('Searching Google Play…'):
                st.session_state.results = search_apps(query)
            st.session_state.selected = []
            if not st.session_state.results:
                st.info('No matches. Enter a different app name or keyword.')
        except ScraperError as exc:
            st.error(str(exc))
    results = st.session_state.get('results', [])
    if results:
        for item in results:
            icon, details = st.columns([1, 10])
            if item['icon_url']:
                icon.image(item['icon_url'], width=48)
            details.write(f"**{item['title']}** · {item['developer']} · Rating: {item['rating'] if item['rating'] is not None else 'Unavailable'}")
            details.link_button('Google Play', item['play_url'])
        ids = st.multiselect('Choose 2–4 competitors', [a['app_id'] for a in results],
            format_func=lambda key: next(a['title']+' ('+key+')' for a in results if a['app_id']==key), key='selected', max_selections=4)
        selected = [a for a in results if a['app_id'] in ids]
        analysis_controls(selected)
    if st.session_state.get('analysis'):
        show_dashboard(st.session_state.analysis)

def analysis_controls(selected):
    count=st.slider('Recent reviews per app',150,300,200,25)
    if st.button('Analyze competitors',type='primary',disabled=not 2<=len(selected)<=4):
        progress=st.progress(0.0,text='Preparing collection…')
        try:
            st.session_state.analysis=analyze(selected,count,progress=lambda fraction,text: progress.progress(fraction,text=text))
            st.session_state.pop('report',None)
            st.session_state.pop('ai_error',None)
        except ValueError as exc:
            st.error(str(exc))
        finally:
            progress.empty()

def show_dashboard(analysis):
    st.divider()
    st.subheader('Competitor comparison')
    st.caption('Analyzed: '+', '.join(a['title'] for a in analysis['apps'])+' · '+analysis['analyzed_at']+' (UTC)')
    st.caption('Dashboard and report reflect this run. Rerun analysis after changing competitors.')
    for warning in analysis['warnings']:
        st.warning(warning)
    summary=comparison(analysis['apps'],analysis['reviews'])
    configuration_columns={key:st.column_config.NumberColumn(key.replace('_',' ').title(),format='percent')
        for key in summary.columns if key.endswith('_percentage')}
    st.dataframe(summary.drop(columns=['app_id']),hide_index=True,column_config=configuration_columns,width='stretch')
    st.caption('Percentages describe collected samples. Blank averages or percentages indicate no usable reviews for that competitor.')
    if not analysis['reviews']:
        st.info('No usable reviews were collected. Try analyzing again; app metadata and the report remain available.')
    else:
        for chart in build_charts(analysis['apps'],analysis['reviews']):
            st.plotly_chart(chart,width='stretch')
    st.subheader('Low-rating feedback')
    frame=review_frame(analysis['reviews'])
    negative=frame[frame.score.isin([1,2])]
    choices={'All competitors':None,**{a['title']+' ('+a['app_id']+')':a['app_id'] for a in analysis['apps']}}
    choice=st.selectbox('Inspect evidence by competitor',list(choices))
    if choices[choice]:
        negative=negative[negative.app_id==choices[choice]]
    if negative.empty:
        st.info('No 1–2 star feedback is available in this sample.')
    else:
        st.dataframe(negative[['app_title','app_id','score','review_text','review_timestamp']],hide_index=True,width='stretch')
    st.subheader('AI Market Gap Analysis')
    key=configuration('GEMINI_API_KEY')
    if not key:
        st.info('Set GEMINI_API_KEY in .env, the environment or Streamlit secrets to enable AI insights. All other features remain available.')
    st.caption('Generates strategic hypotheses from a limited sample of public 1–2 star excerpts. Clicking sends these excerpts to Google Gemini.')
    if st.button('Generate AI insights',disabled=not bool(key) or frame.empty):
        with st.spinner('Analyzing review evidence…'):
            result=generate_insights(analysis['apps'],analysis['reviews'],key,configuration('GEMINI_MODEL','gemini-3.8-flash'))
        if result['error']:
            st.session_state.ai_error=result['error']
        else:
            analysis['ai']=result['data']
            analysis['ai_model']=result.get('model_used')
            analysis['ai_notice']=result.get('notice')
            st.session_state.pop('ai_error',None)
            st.session_state.pop('report',None)
    if st.session_state.get('ai_error'):
        st.warning(st.session_state.ai_error)
    if analysis.get('ai_notice'):
        st.info(analysis['ai_notice'])
    if analysis.get('ai_model'):
        st.caption('AI model used: '+analysis['ai_model'])
    if analysis.get('ai'):
        for section,title in SECTIONS.items():
            st.markdown('#### '+title)
            for item in analysis['ai'].get(section,[]):
                st.write('• '+item)
    st.subheader('Download report')
    try:
        if 'report' not in st.session_state:
            st.session_state.report=build_report(analysis)
        st.download_button('Download Excel report',st.session_state.report,'competitor_report.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception:
        st.error('The Excel report could not be generated. Your analysis is still available. Rerun analysis and retry.')

if __name__ == '__main__':
    main()
