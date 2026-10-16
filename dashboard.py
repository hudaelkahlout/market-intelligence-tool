"""Plotly dashboard figures using current-run evidence."""
import pandas as pd
import plotly.express as px
from market_engine import comparison, review_frame

def build_charts(apps, rows):
    """Return four labeled figures, preserving competitors with zero samples."""
    summary = comparison(apps, rows)
    labels = {'app_title':'Competitor', 'play_rating':'Google Play rating', 'count':'Reviews', 'score':'Stars'}
    rating = px.bar(summary, x='app_title', y='play_rating', title='Competitor Rating Comparison', labels=labels)
    rating.update_yaxes(range=[0,5])
    long = summary.melt(id_vars=['app_id','app_title'], value_vars=['positive_count','neutral_count','negative_count'], var_name='Sentiment', value_name='count')
    long['Sentiment'] = long.Sentiment.str.replace('_count','').str.title()
    distribution = px.bar(long, x='app_title', y='count', color='Sentiment', title='Sentiment Distribution by App',
        labels=labels, color_discrete_map={'Positive':'#208368','Neutral':'#d6a32c','Negative':'#c74949'})
    frame = review_frame(rows)
    stars = []
    for app in apps:
        for score in range(1,6):
            stars.append({'app_title':summary.loc[summary.app_id==app['app_id'],'app_title'].iloc[0], 'score':score,
                'count':int(((frame.app_id==app['app_id']) & (frame.score==score)).sum())})
    star_chart = px.bar(pd.DataFrame(stars), x='score',y='count',color='app_title', barmode='group',
        title='Review Star Distribution', labels={**labels,'app_title':'Competitor'})
    star_chart.update_xaxes(dtick=1)
    negative = px.bar(summary,x='app_title',y='negative_percentage',title='Negative Review Comparison',
        labels={'app_title':'Competitor','negative_percentage':'Share of collected reviews'})
    negative.update_yaxes(range=[0,1],tickformat='.0%')
    for fig in (rating,distribution,star_chart,negative):
        fig.update_layout(legend_title_text='Competitor' if fig is star_chart else 'Sentiment')
    return [rating,distribution,star_chart,negative]
