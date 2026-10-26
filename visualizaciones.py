"""Visualizaciones Plotly revisadas para evitar recortes, leyendas y rótulos solapados.
Los títulos viven en Streamlit, FUERA de los gráficos: responden al ancho del navegador.
"""
from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core.espectros import factor_c
from core.contratos import HISTORICO
from diagnosticos import nombre_edicion

CIAN='#0891B2'; AZUL='#2563EB'; AMBAR='#D97706'; VERDE='#059669';
PIZARRA='#475569'; VIOLETA='#7C3AED'; ROJO='#DC2626'
PALETA=(AZUL, AMBAR, VERDE)
BASE_FONT=dict(family='Inter, Segoe UI, Arial, sans-serif',color='#26354D',size=12)


def estilo(fig, x=None, y=None, height=355, legenda=True, arriba=24):
    fig.update_layout(
        template='plotly_white', paper_bgcolor='#FFFFFF',plot_bgcolor='#FFFFFF',
        font=BASE_FONT, height=height, autosize=True,
        title=None,
        margin=dict(l=60,r=28,t=arriba,b=75 if legenda else 60),
        hoverlabel=dict(bgcolor='white',font_size=12,font_family='Segoe UI'),
        hovermode='closest',
        legend=dict(orientation='h',yanchor='top',y=-.19,xanchor='left',x=0,
                    font=dict(size=11),itemwidth=38) if legenda else dict(visible=False)
    )
    fig.update_xaxes(showline=True,linecolor='#B5C4D6',showgrid=True,gridcolor='#EAF0F7',
                     zerolinecolor='#CDD7E2',ticks='outside',tickcolor='#94A3B8', title_text=x,
                     title_standoff=12,automargin=True)
    fig.update_yaxes(showline=True,linecolor='#B5C4D6',showgrid=True,gridcolor='#EAF0F7',
                     zerolinecolor='#CDD7E2',ticks='outside',tickcolor='#94A3B8',title_text=y,
                     title_standoff=12,automargin=True)
    return fig


def grafico_espectro(r):
    p=r.parametros
    xmax=max(3.2,1.25*p['tl'],1.25*max(r.periodos))
    ts=np.linspace(.0001,xmax,700)
    C=factor_c(ts,p['tp'],p['tl'],r.edicion)
    ag=p['z']*p['u']*p['s']*C/p['r']
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=ts,y=ag,mode='lines',name='Sa/g · '+nombre_edicion(r.edicion),
                             line=dict(color=AZUL,width=3),fill='tozeroy',
                             fillcolor='rgba(37,99,235,0.08)',hovertemplate='T=%{x:.3f} s · Sa/g=%{y:.4f}<extra></extra>'))
    for i,t in enumerate(r.periodos):
        sa=float(r.espectro.iloc[i]['Sa_m_s2'])/p['gravedad']
        fig.add_trace(go.Scatter(x=[t],y=[sa],mode='markers',name=f'Modo {i+1} · {t:.3f} s',
                                 marker=dict(size=12,color=PALETA[i],line=dict(width=2,color='white')),
                                 hovertemplate=f'Modo {i+1}<br>T={t:.3f} s<br>Sa/g={sa:.4f}<extra></extra>'))
    for val,etiqueta in [(p['tp'],'Tₚ'),(p['tl'],'Tₗ')]:
        fig.add_vline(x=val,line_dash='dot',line_color='#94A3B8',line_width=1)
        fig.add_annotation(x=val,y=1,xref='x',yref='paper',text=f'{etiqueta}={val:g}s',showarrow=False,yshift=8,font=dict(size=10))
    estilo(fig,'T (s)','Sa / g',height=420)
    contexto(fig,r,'Espectro reducido')
    fig.update_xaxes(range=[0,xmax]);fig.update_yaxes(rangemode='tozero')
    return fig


def grafico_participacion(r):
    d=r.participacion
    fig=go.Figure()
    fig.add_bar(x=d.Modo,y=d.Participacion_pct,name="Individual",
                marker_color=AZUL,width=.45)
    fig.add_scatter(x=d.Modo,y=d.Participacion_acumulada_pct,
                    name="Acumulada",mode="lines+markers",
                    line=dict(color=AMBAR,width=3))
    fig.add_scatter(x=[.6,3.4],y=[90,90],name="Umbral 90%",
                    mode="lines",line=dict(color=PIZARRA,dash="dot"))
    estilo(fig,"Modo","Masa efectiva (%)",height=420)
    fig.update_xaxes(tickvals=[1,2,3])
    fig.update_yaxes(range=[0,(100 if float(d.Participacion_acumulada_pct.max())<=100.01 else float(d.Participacion_acumulada_pct.max())*1.04)])
    contexto(fig,r,"Masa efectiva · eje único")
    return fig


def grafico_formas(r):
    n=len(r.datos)
    pisos=np.arange(n+1)
    fig=go.Figure()
    for j in range(3):
        v=r.datos[f'Modo_{j+1}'].to_numpy(float)
        norm=np.max(np.abs(v))
        norm=norm if norm>0 else 1
        fig.add_trace(go.Scatter(x=np.r_[0,v/norm],y=pisos,mode='lines+markers',name=f'Modo {j+1}',
                                 line=dict(width=2.8,color=PALETA[j]),marker=dict(size=8),
                                 hovertemplate='Piso %{y}<br>φ/|φ|max=%{x:.3f}<extra></extra>'))
    fig.add_vline(x=0,line_color='#A9B8CC',line_width=1)
    estilo(fig,'φ / max |φ| (—)','Piso',height=420)
    contexto(fig,r,'Formas suministradas')
    fig.update_yaxes(tickmode='array',tickvals=list(range(n+1)),range=[0,n+.3]);fig.update_xaxes(range=[-1.15,1.15])
    return fig


def grafico_fuerzas(r):
    pisos=r.datos['Piso'].to_numpy(int)
    fig=go.Figure()
    for j in range(3):
        fig.add_trace(go.Bar(x=r.fuerzas[:,j],y=[f'P{p}' for p in pisos],orientation='h',
                             name=f'Modo {j+1}',marker_color=PALETA[j],
                             hovertemplate='Piso %{y}<br>F=%{x:.2f} kN<extra></extra>'))
    fig.update_layout(barmode='group',bargap=.24)
    estilo(fig,'F (kN)','Piso',height=420)
    contexto(fig,r,'Fuerzas de piso · con signo')
    fig.add_vline(x=0,line_color='#64748B',line_width=1)
    return fig


def grafico_cortantes(r):
    pisos=r.datos['Piso'].to_numpy(int)
    fig=go.Figure()
    for j in range(3):
        fig.add_trace(go.Scatter(x=np.r_[r.cortantes[::-1,j],r.cortantes[0,j]],y=np.r_[pisos[::-1],0],mode='lines+markers',name=f'Modo {j+1}',
                                 line=dict(width=2.8,color=PALETA[j],shape='vh'),marker=dict(size=8),
                                 hovertemplate='Piso %{y}<br>V=%{x:.2f} kN<extra></extra>'))
    fig.add_vline(x=0,line_color='#64748B',line_width=1)
    estilo(fig,'V (kN)','Piso',height=420)
    contexto(fig,r,'Cortante en cada entrepiso')
    fig.update_yaxes(tickmode='array',tickvals=[0,1,2,3,4,5],range=[0,5.2]);return fig


def grafico_combinacion(r):
    """Separar mezcla 0-170 kN de amplificación ET1 ~850 kN: no ocultar escalas."""
    c=r.combinacion; fig=make_subplots(rows=1,cols=2,column_widths=[.57,.43],
                horizontal_spacing=.16,subplot_titles=('COMBINACIÓN 25/75','HISTÓRICA · NO DISEÑO'))
    for campo,etiqueta,color in [('Vsum_abs_kN','Σ |Vᵣ|',PIZARRA),
                                ('Vrcsc_kN','SRSS',VIOLETA),
                                ('Vrnc_h_kN','0.25 abs + 0.75 SRSS',AMBAR)]:
        fig.add_trace(go.Scatter(x=np.r_[c[campo].to_numpy()[::-1],c[campo].iloc[0]],y=np.r_[c['Piso'].to_numpy()[::-1],0],mode='lines+markers',name=etiqueta,
                      line=dict(color=color,width=2.7,shape='vh'),marker=dict(size=7),
                      hovertemplate='Piso %{y}<br>%{x:.2f} kN<extra></extra>'),row=1,col=1)
    fig.add_trace(go.Scatter(x=np.r_[c['Vreal_kN'].to_numpy()[::-1],c['Vreal_kN'].iloc[0]],y=np.r_[c['Piso'].to_numpy()[::-1],0],mode='lines+markers',name='Histórica ET1 · no diseño',
                       line=dict(width=3.5,color=CIAN,shape='vh'),marker=dict(size=9),
                       hovertemplate='Piso %{y}<br>ET1 %{x:.2f} kN<extra></extra>'),row=1,col=2)
    estilo(fig,None,None,height=425,arriba=64)
    fig.update_annotations(font=dict(color='#475569',size=11),yshift=5)
    fig.update_xaxes(title_text='Cortante (kN)',row=1,col=1,automargin=True)
    fig.update_xaxes(title_text='Cortante ET1 (kN)',row=1,col=2,automargin=True)
    fig.update_yaxes(title_text='Piso',tickmode='array',tickvals=[0,1,2,3,4,5],range=[0,5.2],row=1,col=1)
    fig.update_yaxes(tickmode='array',tickvals=[0,1,2,3,4,5],range=[0,5.2],row=1,col=2)
    fig.update_layout(margin=dict(l=56,r=28,t=90,b=125),legend=dict(orientation='h',y=-.25,x=0,itemsizing='constant',font=dict(size=10)))
    contexto(fig,r,'Combinación / referencia histórica')
    return fig


def grafico_sensibilidad(df, parametro):
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=df['Valor'],y=df['Vcombinado_kN'],mode='lines+markers',name='V combinada',
                             line=dict(color=AZUL,width=3),marker=dict(size=5)))
    fig.add_trace(go.Scatter(x=df['Valor'],y=df['Vreal_ET1_kN'],mode='lines+markers',name='Vreal · ET1',
                             line=dict(color=CIAN,width=3),marker=dict(size=5),yaxis='y2'))
    estilo(fig,parametro,'Combinación (kN)',height=385)
    fig.update_layout(yaxis2=dict(title='Vreal ET1 (kN)',overlaying='y',side='right',showgrid=False,
                                  title_standoff=10,automargin=True),margin=dict(l=65,r=73,t=28,b=90))
    return fig



def contexto(fig,r,titulo):
    """Título incluido en PNG; texto breve evita depender del encabezado externo."""
    fig.add_annotation(x=0,y=1.18,xref="paper",yref="paper",
                       xanchor="left",text=titulo+"<br>"+nombre_edicion(r.edicion),
                       showarrow=False,align="left",font=dict(size=11,color=PIZARRA))
    fig.update_layout(margin=dict(t=90,b=115),meta={
        "firma":r.firma,"edicion":r.edicion,"estado":r.estado})
    return fig

def grafico_combinado(r):
    """Solo magnitudes de combinación; histórica permanece en panel secundario."""
    fig=go.Figure()
    for campo,nombre,color in [
        ("Vsum_abs_kN","Σ |V|",PIZARRA),
        ("Vrcsc_kN","SRSS",VIOLETA),
        ("Vrnc_h_kN","25/75",AZUL)]:
        fig.add_scatter(x=np.r_[r.combinacion[campo].to_numpy()[::-1],r.combinacion[campo].iloc[0]],y=np.r_[r.datos.Piso.to_numpy()[::-1],0],
                        mode="lines+markers",name=nombre,
                        line=dict(color=color,width=3,shape="vh"))
    estilo(fig,"V (kN)","Piso",height=460)
    fig.update_yaxes(tickvals=[0,1,2,3,4,5],range=[0,5.2])
    return contexto(fig,r,"Combinación de cortantes")

def tiempos_animacion(r,modo,ralentizacion=8):
    t=float(r.periodos[modo-1])
    n=60
    duration=max(16.,1000*t*ralentizacion/n)
    return np.linspace(0,t,n+1),duration,duration*n/(1000*t)

def grafico_edificio_2d(r,modo=1,amplificacion=1.8):
    """Un ciclo sinusoidal con reloj modal; reproducción ralentizada explícita."""
    phi=np.r_[0,r.datos[f"Modo_{modo}"].to_numpy(float)]
    phi/=np.max(np.abs(phi))
    alturas=np.arange(6)*r.parametros["altura_piso"]
    tiempos,duracion,lento=tiempos_animacion(r,modo)
    periodo=r.periodos[modo-1]
    def coords(t):
        off=amplificacion*phi*np.sin(2*np.pi*t/periodo)
        x=[];y=[]
        for k in range(6):
            x.extend([off[k]-1,off[k]+1,None]);y.extend([alturas[k],alturas[k],None])
        for lateral in [-1,1]:
            for k in range(5):
                x.extend([lateral+off[k],lateral+off[k+1],None])
                y.extend([alturas[k],alturas[k+1],None])
        return x,y
    frames=[]
    for i,t in enumerate(tiempos):
        x,y=coords(t)
        frames.append(go.Frame(name=str(i),data=[go.Scatter(x=x,y=y)],
                               layout=go.Layout(annotations=[
                                   dict(x=0,y=1.12,xref="paper",yref="paper",
                                        xanchor="left",showarrow=False,
                                        text=f"Modo {modo} · t={t:.4f} s · T={periodo:.4f} s",
                                        font=dict(size=11))])))
    x,y=coords(0)
    fig=go.Figure(data=[go.Scatter(x=x,y=y,mode="lines",
                                  line=dict(color=CIAN,width=4),name="Esquema modal")],
                  frames=frames)
    estilo(fig,"Amplitud relativa (—)","Altura (m)",height=510,legenda=False)
    fig.update_xaxes(range=[-4.5,4.5])
    fig.update_yaxes(range=[-.3,alturas[-1]+.5],dtick=r.parametros["altura_piso"])
    fig.add_annotation(x=0,y=1.12,xref="paper",yref="paper",xanchor="left",
                       text=f"Modo {modo} · t=0 s · T={periodo:.4f} s",showarrow=False,
                       font=dict(size=11))
    fig.update_layout(margin=dict(t=65,b=120,l=55,r=20),meta={
        "periodo_s":float(periodo),"ralentizacion":lento,
        "tiempos_s":tiempos.tolist(),"firma":r.firma,"estado":r.estado},
        updatemenus=[dict(type="buttons",direction="left",x=0,y=-.22,
            showactive=False,buttons=[
              dict(label="▶ Reproducir",method="animate",args=[None,dict(
                  frame=dict(duration=duracion,redraw=False),transition=dict(duration=0),
                  fromcurrent=False,mode="immediate")]),
              dict(label="Ⅱ Pausar",method="animate",args=[[None],dict(
                  frame=dict(duration=0,redraw=False),transition=dict(duration=0),
                  mode="immediate")])])])
    return fig

def grafico_edificio(r,modo=1,amplificacion=1.8):
    """Constructor 3D opcional; no se presenta como verificado en la UI."""
    phi=np.r_[0,r.datos[f"Modo_{modo}"].to_numpy(float)]
    phi/=np.max(np.abs(phi))
    z=np.arange(6)*r.parametros["altura_piso"]
    tiempos,duracion,lento=tiempos_animacion(r,modo)
    frames=[go.Frame(name=str(i),data=[go.Scatter3d(
        x=amplificacion*phi*np.sin(2*np.pi*t/r.periodos[modo-1]),
        y=np.zeros(6),z=z)]) for i,t in enumerate(tiempos)]
    fig=go.Figure([go.Scatter3d(x=np.zeros(6),y=np.zeros(6),z=z,
                               mode="lines+markers",line=dict(color=CIAN,width=5))],
                   frames=frames)
    fig.update_layout(height=460,scene=dict(xaxis_title="Amplitud relativa",
                        yaxis_title="Esquema",zaxis_title="Altura (m)"),
                      meta={"verificacion":"NO_VERIFICADO_WEBGL","firma":r.firma})
    return fig
