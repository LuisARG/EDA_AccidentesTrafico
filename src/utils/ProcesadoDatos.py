# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd

def get_anio_excel(nombre_excel):
    ind_aux = nombre_excel.rfind('.')
    return int(nombre_excel[ind_aux-4:ind_aux])

class ProcesadorDFConductores:
    '''
    La clase ProcesadorDFConductores se encarga del tratamiento de los EXCEL
    con información de conductores implicados en accidentes con víctimas por sexo con métodos para:
    * Determinar el nombre de la hoja con información de “Conductores implicados en accidentes con víctimas clasificados por edad,
      sexo y condición, en vías interurbanas.” Y la hoja con la misma información pero para vías urbanas.
    * En cada tipo de EXCEL determinar el subconjunto de filas y columnas donde extrear la información
    * Parsear los rangos de edades con el fin de generar dos columnas con el inicio del rango y con el final del rango
    * Eliminar filas con subtotales
    * Estandarizar los campos de rango de edad y sexo
    * Concatenar los diferentes EXCEL en un único Dataset
    '''
    
    '''
    Constructor
    
    Argumentos:
    * debug: si toma valor True, esta clase mostrará mensajes de debug
    '''
    def __init__(self, debug=False):
        self.__debug = debug
        
    def __convertir_sexo(self, sexo):
        sexo_convertido = sexo
        
        if sexo == "V":
            sexo_convertido = "Hombre"
        elif sexo == "M":
            sexo_convertido = "Mujer"
        elif sexo == "Se desconoce":
            sexo_convertido = "Desconocido"
        
        return sexo_convertido
    
    def __rellenar_nulos_edades(self, df, anio):
        if anio >= 2006:
            for ind in range(len(df)):
                aux = ind % 3
                if (aux == 1) or (aux == 2):
                    df.iat[ind,1] = df.iat[ind-aux,1]
        else:
            for ind in range(len(df)):
                if ind % 2 == 1:
                    df.iat[ind,1] = df.iat[ind-1,1]
            
    def __convertir_rango_edades(self, rango_edades):
        conversion = np.nan
        rango_edades = rango_edades.strip().upper().replace("Á","A")
        if rango_edades.startswith("HASTA"):
            conversion = rango_edades.replace("HASTA ", "0-").replace(" AÑOS", "")                        
        elif rango_edades.startswith("DE") and rango_edades.endswith("MAS"):
            conversion = rango_edades.replace("DE ", "").replace(" O MAS", "-")            
        elif rango_edades.startswith("DE"):
            conversion = rango_edades.replace("DE ", "").replace(" AÑOS", "").replace(" A ", "-")
        elif rango_edades.startswith("DE"):
            conversion = rango_edades.replace("DE ", "").replace(" AÑOS", "").replace(" A ", "-")
        elif rango_edades.startswith("MAS DE"):
            aux = rango_edades.replace("MAS DE ", "").replace(" AÑOS", "")
            conversion = str(int(aux)+1) + "-"
        
        return conversion
            
        
    def __convertir_columna_rango_edades(self, df):
        df['Rango Edades'] = df['Rango Edades'].apply(self.__convertir_rango_edades)
            

    def __desdoblar_rango_edades(self, rango_edades):
        inicios_rango = []
        finales_rango = []
        for rango in rango_edades:
            if type(rango) != str:
                inicios_rango.append(np.nan)
                finales_rango.append(np.nan)
            else:
                edades = rango.split("-")
                if len(edades[1]) == 0:
                    inicios_rango.append(edades[0])
                    finales_rango.append(999)
                else:
                    inicios_rango.append(edades[0])
                    finales_rango.append(edades[1])
         
        return (pd.Series(inicios_rango), pd.Series(finales_rango))
                
    def anio2nombrehoja(self, anio, es_interurbano):
        '''
        Devuelve el nombre de la hoja EXCEL con información a nivel de vías interurbanas.
        Dicho nombre depebde del año del EXCEL y de si la información contenida es
        de vías interurbanas o urbanas.
        
        Argumentos:
        * anio: año del EXCEL
        * es_interurbano: True para información de vías interurbanas y False para el de urbanas
        
        Resultado:
        * El nombre de la hoja EXCEL
        '''
        nombrehoja = None
        if anio >= 2015 and anio <= 2019:
            if es_interurbano:
                nombrehoja = 'TABLA 4.2.I'
            else:
                nombrehoja = 'TABLA 4.2.U'
        elif anio >= 2011 and anio <= 2014:
            if es_interurbano:
                nombrehoja = '4.2.I'
            else:
                nombrehoja = '4.2.U '
        elif anio >= 2006 and anio <= 2010:
            if es_interurbano:
                nombrehoja = '4.2.C. '
            else:
                nombrehoja = '4.2.U. '
        elif anio >= 1999 and anio <= 2005:
            if es_interurbano:
                nombrehoja = '4.2.C.'
            else:
                nombrehoja = '4.2.U.'
        elif anio == 1998:
            if es_interurbano:
                nombrehoja = '4.2 C'
            else:
                nombrehoja = '4.2 U'

        return nombrehoja
 
    def get_conductores_x_sexo_anios(self, df, anio):
        '''
        Crea un DataFrame con los totales de conductores por Sexo por rango de años para un año dado.
        
        Argumentos:
        * df: DataFrame con información a nivel de vías interurbanas o vías urbanas,
              tal como se carga de la hoja EXCEL
        * anio: año de la información recibida en 'df'
        
        Resultado:
        * El DataFrame
        '''
        valor_buscado = None
        rango_edades_buscado = None
        if anio >= 2015 and anio <= 2019:
            valor_buscado = 'HOMBRE'
            rango_edades_buscado = 'SE DESCONOCE'
        elif anio >= 1998 and anio <= 2014:
            valor_buscado = 'V'
            rango_edades_buscado = 'NO ESPECIFICADA'
        
        # Buscar primera fila con datos de conductores por rango de edades
        if self.__debug:
            print("Buscar",valor_buscado)
        ind_ini_hombre = None
        ind_aux = 0
        while ind_ini_hombre == None:
            celda = df.iat[ind_aux,1]
            if type(celda) == str and (celda.upper() == valor_buscado):
                ind_ini_hombre = ind_aux
            ind_aux += 1
        
        # Buscar ultima fila con datos de conductores por rango de edades
        if self.__debug:
            print("Buscar",rango_edades_buscado)
        ind_fin_hombre = None
        ind_aux = -1
        while ind_fin_hombre == None:
            celda = df.iat[ind_aux,0]
            if type(celda) == str and (celda.upper() == rango_edades_buscado):
                ind_fin_hombre = ind_aux
            ind_aux -= 1
        
        if self.__debug:
            print("Crear df_resultado")
        df_resultado = df.iloc[ind_ini_hombre:ind_fin_hombre+3,0:3].copy()
        df_resultado.columns = ['Rango Edades', 'Sexo', 'Total']
        df_resultado.insert(loc=0, column='Año', value=anio)
        df_resultado['Sexo'] = df_resultado['Sexo'].apply(self.__convertir_sexo)
        if self.__debug:
            print("Sexo convertido")
        
        df_resultado = df_resultado[df_resultado['Sexo'] != 'Total']
        if self.__debug:
            print("Filas total eliminadas")
        df_resultado.reset_index(drop=True, inplace=True)
        self.__rellenar_nulos_edades(df_resultado, anio)
        if self.__debug:
            print("Fin __rellenar_nulos_edades")
        self.__convertir_columna_rango_edades(df_resultado)
        if self.__debug:
            print("Fin __convertir_columna_rango_edades")
        
        return df_resultado

    def unir_conductores_x_sexo_anio(self, df_interurbana, df_urbana):
        '''
        Crea un DataFrame único para un año uniendo la información de vías interurbanas y de vías urbanas.
        Argumentos:
        * df_interurbana: DataFrame con la información de vías interurbanas
        * df_iurbana: DataFrame con la información de vías urbanas
        
        Resultado:
        * DataFrame unión de la información de vías interurbanas y de vías urbanas
        '''
        df_union = df_interurbana.copy()
        df_union.rename(columns={"Total": "Total Interurbana"}, inplace=True)
        df_union["Total Urbana"] = df_urbana["Total"]
        df_union["Total"] = df_union["Total Interurbana"] + df_union["Total Urbana"]
        ini_fin_rangos = self.__desdoblar_rango_edades(df_union['Rango Edades'])
        df_union.insert(loc=2, column='Ini Rango Edades', value=ini_fin_rangos[0])
        df_union.insert(loc=3, column='Fin Rango Edades', value=ini_fin_rangos[1])
        
        return df_union
 
    def unir_conductores_x_sexo_anios(self, lista_df):
        '''
        Crea un DataFrame único con la información de todos los años.
        Argumentos:
        * lista_df: Lista con Dataframes de cada años
        
        Resultado:
        * DataFrame unión de todos los DataFrame recibidos en 'lista_df'
        '''
        union = lista_df[0].copy()
        for ind in range(1,len(lista_df)):
            union = union.append(lista_df[ind])
            
        return union
            