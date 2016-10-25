from django.shortcuts import render
import pandas as pd
import datetime
import time
from django.http import HttpResponse
import plotly as plty
from django.core.cache import cache
from .models import utilities_id

def index(request):

    all_utilities = utilities_id.objects.all()
    all_utilities = pd.DataFrame(list(utilities_id.objects.all()))
    all_utilities = all_utilities["utility_name"]
    print(all_utilities)
    context = {"all_utilities": all_utilities}      

    return render (request,"index.html", context)

def AdvancedSearch (request):
    if request.method == "GET":
        zipcode = request.GET.get('zipcode','')
        utility = request.GET.get('utility','')
        sector_list = request.GET.getlist('checkbox_sector')
        rate_display_req = False

    url = "http://api.openei.org/utility_rates?version=3"
    authentification_key = "zLCFKYVhy0uj6ZYNZW28BwOcdvm47tF4LGwuWMug"

    if not (utility == "" or len(sector_list)==0):
        rate_display_req = True
        sector = sector_list[0] #only one choice allowed
        url_request = url + "&format=csv" + "&api_key=" + str(authentification_key) + "&eia=" + str(14328) + "&detail=full"
        response = pd.read_csv(url_request)
        df_raw_data = pd.DataFrame(response)
        request.session['url_request'] = str(url_request)
        request.session['sector'] = str(sector)
        df_raw_data = df_raw_data.loc[(df_raw_data["sector"]==sector)]
        rate_list = df_raw_data["name"]
        cache.set("df_raw_data", df_raw_data,600)
        context = {"rate_list" : rate_list , "df_raw_data" : df_raw_data , "rate_display_req":rate_display_req
                   }

    else:
        rate_display_req = False
        context = {"rate_display_req":rate_display_req}
    return render (request,"index.html",context)

def ratestructure (request):

    if request.method == "GET":
        pick_rate_1 = request.GET.get('pick_rate_1','')
        pick_rate_2 = request.GET.get('pick_rate_2','')
        l = [pick_rate_1, pick_rate_2]

    sector = request.session['sector']
    df_raw_data = cache.get("df_raw_data")
    df_master_tariff = df_raw_data.loc[(df_raw_data["sector"] == sector)]

    list_schedules = []
    list_of_structures = []
    for tariff_name in l:
        df_tariff = df_master_tariff.loc[df_master_tariff["name"] == str(tariff_name), :].reset_index(drop=True)
        Max_start_date = max(df_tariff["startdate"])
        df_tariff = df_tariff.loc[df_tariff["startdate"] == Max_start_date, :].reset_index(drop=True)
        df_tariff = df_tariff.dropna(axis=1, how="any")
        df_schedule = df_tariff.ix[:,"energyweekdayschedule_jan_0":]

        for column in df_schedule:
            if ("weekend" not in column) and ("weekday" not in column):
                del df_schedule[column]

        max_period = df_schedule.max(axis=1)[0]
        list_period = ["Period " + str(i) for i in range(max_period + 1)]
        max_tiers = 0
        for column in df_tariff:
            if "energyratestructure/period" in column:
                max_tiers = max(int(column[32]), max_tiers)

        df_price = pd.DataFrame(columns=list_period, index=range(max_tiers + 1))
        df_tiermax = pd.DataFrame(columns=list_period, index=range(max_tiers + 1))

        for period_nbr in range(max_period + 1):
            tier_idx = 0
            for column in df_tariff:
                column_name = "energyratestructure/period" + str(period_nbr)
                if (column_name in column) and (column.count("max") == 1):
                    df_tiermax.ix[tier_idx, period_nbr] = df_tariff.ix[0, column]
                elif (column_name in column) and (column.count("rate") == 2):
                    df_price.ix[tier_idx, period_nbr] = df_tariff.ix[0, column]
                    tier_idx += 1

            df_price = df_price.fillna(value=-1)
            df_tiermax = df_tiermax.fillna(value=-1)

            list_of_structures.append([df_price, df_tiermax])
            list_schedules.append(df_schedule)


    df_price_1 = list_of_structures[0][0]
    df_tiermax_1 = list_of_structures[0][1]
    df_price_2 = list_of_structures[1][0]
    df_tiermax_2 = list_of_structures[1][1]
    df_price_1.to_html('/Users/samyouardini/Desktop/DealEng/templates/df_price_1.html')
    df_price_2.to_html('/Users/samyouardini/Desktop/DealEng/templates/df_price_2.html')
    df_tiermax_1.to_html('/Users/samyouardini/Desktop/DealEng/templates/df_tiermax_1.html')
    df_tiermax_2.to_html('/Users/samyouardini/Desktop/DealEng/templates/df_tiermax_2.html')
    list_price = [df_price_1, df_price_2]
    list_tiers =[df_tiermax_1, df_tiermax_2]
    cache.set ("list_price",list_price,6000)
    cache.set("list_tiers", list_tiers, 6000)
    cache.set("list_schedules", list_schedules, 6000)
    cache.set("l",l, 6000)



    context = {"df_price_1": df_price_1,
                       "df_price_2": df_price_2, "df_tiermax_1": df_tiermax_1, "df_tiermax_2": df_tiermax_2,
                       "pick_rate_1": pick_rate_1, "pick_rate_2": pick_rate_2}

    return render(request, "rate_structure.html", context)

def Savings (request):
        BILLS = []
        list_master = []
        list_price = cache.get("list_price")
        list_tiers = cache.get("list_tiers")
        list_schedules = cache.get("list_schedules")
        print(len(list_tiers))
        l = cache.get("l")
        pick_rate_1 = l[0]
        pick_rate_2 = l[1]
        for x in range(0,2):
            df_price = list_price[x]
            df_tiermax = list_tiers[x]
            df_schedule = list_schedules[x]


            df_energy_consumption = pd.read_csv("/Users/samyouardini/Documents/1 - Savings Forecasting/3 - Energy profiles/load_AddressID_62904_MeterID_[ 12684.].csv")
            df_PV_production = pd.read_csv("/Users/samyouardini/Documents/1 - Savings Forecasting/4 - PV production/Production_AddressID_64764_SystemID_[ 121795.].csv")
            df_PV_production = df_PV_production.ix[:, 1]
            df_energy_consumption = df_energy_consumption.ix[:, :"Electricity:Facility [kW](Hourly)"]
            df_master = pd.DataFrame(columns=["Datetime", "Hourly electricity production", "Hourly electricity consumption",
                         "Net Hourly electricity consumption", "Daily electricity consumption", "Period",
                         "Tier", "Rate", "Electricity bill"], index=range(8760))
            df_master["Datetime"] = df_energy_consumption.ix[:, 0]
            df_master["Datetime"] = df_master.Datetime.apply(lambda str_date: datetime.datetime.fromtimestamp(
                time.mktime(time.strptime(str_date[0:16], "%Y-%m-%d %H:%M"))))
            df_master["Hourly electricity consumption"] = df_energy_consumption.ix[:, 1]
            df_master["Hourly electricity production"] = pd.Series(df_PV_production)
            df_master["Net Hourly electricity consumption"] = df_master["Hourly electricity consumption"].sub(
                df_master["Hourly electricity production"], fill_value=0)
            list_temp_period = []
            list_month = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

            for idx, date_time in df_master["Datetime"].iteritems():
                if date_time.weekday() <= 4:
                    list_col_bool_weekday = [(list_month[date_time.month - 1] in column) & ("weekday" in column) & (
                        (int(date_time.hour)) == int(column[26:])) for column in df_schedule]
                    list_temp_period.append(df_schedule.loc[[True], list_col_bool_weekday].ix[0, 0])
                else:
                    list_col_bool_weekend = [(list_month[date_time.month - 1] in column) & ("weekend" in column) & (
                        int((date_time.hour)) == int(column[26:])) for column in df_schedule]
                    list_temp_period.append(df_schedule.loc[[True], list_col_bool_weekend].ix[0, 0])
            df_master["Period"] = pd.Series(list_temp_period)
            list_tier_temp = []
            list_rate_temp = []
            list_positive_consumption = []
            zero = 0
            for positive in df_master["Net Hourly electricity consumption"]:
                if positive >= 0:
                    list_positive_consumption.append(positive)
                else:
                    list_positive_consumption.append(zero)
            df_master["Daily electricity consumption"] = list_positive_consumption

            list_daily_consumption_temp = []
            daily_consumption = 0
            for idx, hourly_consumption in df_master["Daily electricity consumption"].iteritems():
                date_time = df_master["Datetime"].ix[idx, 0]
                if date_time.hour == 0:
                    daily_consumption = hourly_consumption
                else:
                    daily_consumption += hourly_consumption
                list_daily_consumption_temp.append(daily_consumption)
                for idx2, tier_max in df_tiermax["Period " + str(df_master["Period"].ix[idx, :])].iteritems():
                    if daily_consumption <= tier_max:
                        list_tier_temp.append(idx2)
                        list_rate_temp.append(df_price.ix[idx2, df_master["Period"].ix[idx, 0]])
                        break
                    elif tier_max == -1:
                        list_tier_temp.append(idx2)
                        list_rate_temp.append(df_price.ix[idx2, df_master["Period"].ix[idx, 0]])
                        break

            df_master["Daily electricity consumption"] = pd.Series(list_daily_consumption_temp)
            df_master["Tier"] = pd.Series(list_tier_temp)
            df_master["Rate"] = pd.Series(list_rate_temp)
            df_master["Hourly electricity production"] = pd.Series(df_PV_production)
            list_temp_electricity_bill = []
            nbc = 0.023
            for idx3, Netx3 in df_master["Net Hourly electricity consumption"].iteritems():
                if Netx3 <= 0:
                    list_temp_electricity_bill.append(df_master["Rate"].iloc[idx3])
                elif Netx3 > 0:
                    list_temp_electricity_bill.append(df_master["Rate"].iloc[idx3] + nbc)

            df_master["Rate"] = pd.Series(list_temp_electricity_bill)
            df_master["Electricity bill"] = df_master["Net Hourly electricity consumption"].multiply(df_master["Rate"])
            df_master.to_csv("/Users/samyouardini/Desktop/df_master.csv")

            Total_bill = 0
            for bill in df_master["Electricity bill"]:
                Total_bill = Total_bill + bill
            BILLS.append(Total_bill)
            list_master.append(df_master)

        Savings = format(((BILLS[1]-BILLS[0])/BILLS[0])*100, '.1f')
        Savings_rate_1 = format(BILLS[0], '.1f')
        Savings_rate_2 = format(BILLS[1], '.1f')
        cache.set("list_master","list_master", 3000)
        print (BILLS, Savings)
        context = {"BILLS":BILLS , "Savings":Savings, "pick_rate_1":pick_rate_1, "pick_rate_2":pick_rate_2 , "Savings_rate_1":Savings_rate_1 , "Savings_rate_2" :Savings_rate_2 }

        return render(request, "Savings.html", context)


def import_db(request):
    f_path= '/Users/samyouardini/Desktop/Classeur2.xlsx'
    f = pd.read_excel(f_path)

    for name in f["name"]:
        tmp = utilities_id.objects.create()
        tmp.utility_name = name
        tmp.save()

    for id in f["id"]:
        tmp = utilities_id.objects.create()
        tmp.utility_id = id
        tmp.save()

    return HttpResponse("Data base updated")