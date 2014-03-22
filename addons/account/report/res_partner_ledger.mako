<html>
<head>
    <style type="text/css">
        ${css}
			.list_sale_table {
			border:thin solid #E3E4EA;
			text-align:center;
			border-collapse: collapse;
			}
			.list_sale_table td {
			border-top : thin solid #EEEEEE;
			text-align:right;
			font-size:12;
			padding-right:3px
			padding-left:3px
			padding-top:3px
			padding-bottom:3px
			}

			.list_bank_table {
			text-align:center;
			border-collapse: collapse;
			}
			.list_bank_table td {
			text-align:left;
			font-size:12;
			padding-right:3px
			padding-left:3px
			padding-top:3px
			padding-bottom:3px
			}

			.list_bank_table th {
			background-color: #EEEEEE;
			text-align:left;
			font-size:12;
			font-weight:bold;
			padding-right:3px
			padding-left:3px
			}
			
			.list_sale_table th {
			background-color: #EEEEEE;
			border: thin solid #000000;
			text-align:center;
			font-size:12;
			font-weight:bold;
			padding-right:3px
			padding-left:3px
			}
			
			.list_table thead {
			    display:table-header-group;
			}


			.list_tax_table {
			}
			.list_tax_table td {
			text-align:left;
			font-size:12;
			}
			
			.list_tax_table th {
			}


			.list_table thead {
			    display:table-header-group;
			}


			.list_total_table {
				border-collapse: collapse;
			}
			.list_total_table td {
			text-align:right;
			font-size:12;
			}

			.no_bloc {
				border-top: thin solid  #ffffff ;
			}

			
			.list_total_table th {
				background-color: #F7F7F7;
				border-collapse: collapse;
			}

            tfoot.totals tr:first-child td{
                padding-top: 15px;
            }



			.right_table {
			right: 4cm;
			width:"100%";
			}
			
			.std_text {
				font-size:12;
				}


    </style>
</head>
<body>
    <%page expression_filter="entity"/>
    <%
    bal=0
    curr_bal=0
    def carriage_returns(text):
        return text.replace('\n', '<br />')

    %>
    %for p in objects:

    <h1 style="clear:both;">Partner Ledger</h1>

    <table class="basic_table" width="100%">
        <tr>
            <td style="font-weight:bold;">${_("Customer Ref")}</td>
            <td style="font-weight:bold;">${_("Customer Name")}</td>
            <td style="font-weight:bold;"></td>
        </tr>
        <tr>
            <td>${p.ref}</td>
	    <td>${p.name}</td>
            <td></td>
        </tr>
    </table>
    

    <table class="basic_table" width="100%" align="right">
        <tr>
            <td style="font-weight:bold;">Date</td>
            <td style="font-weight:bold;">JRNL</td>
            <td style="font-weight:bold;">Account</td>
            <td style="font-weight:bold;">Move Name</td>
            <td style="font-weight:bold;">Name</td>
	    <td style="font-weight:bold;">Reconcile</td>
            <td style="font-weight:bold;">Debit</td>
	    <td style="font-weight:bold;">Credit</td>
	    <td style="font-weight:bold;">Balance</td>
	    %if display_currency:
	       <td style="font-weight:bold;">Currency</td>
            %endif
        </tr>
	%for line in sorted(lines(p),key=lambda a:(a['date'])):
	<%
	bal=bal+line['debit']-line['credit']
	rec=line.get('reconcile','')
	curr_bal=curr_bal+line['amount_currency']
	curr = line.get('currency_code','')
	if curr == None:
	   curr=''
        if line['a_code']=='OPEJ':
           continue
	%>
        <tr>
            <td>${formatLang(line['date'],date=True)}</td>
	    <td>${line['code']}</td>
            <td>${line['a_code']}</td>
            <td>${line['move_name']}</td>
            <td>${line['name']}</td>
	    <td>${rec}</td>
            <td align="right">${formatLang(line['debit'])}</td>
            <td align="right">${formatLang(line['credit'])}</td>
	    <td align="right">${company.currency_id.symbol}${formatLang(bal)}</td>
            %if display_currency:
	       <td align="right">${formatLang(line['amount_currency'])} ${curr}</td>
            %endif
        </tr>
	%endfor
        <tr>
            <td></td>
	    <td></td>
            <td></td>
            <td></td>
            <td></td>
	    <td></td>
            <td style="font-weight:bold;" align="right">${sum_debit_partner(p)}</td>
            <td style="font-weight:bold;" align="right">${sum_credit_partner(p)}</td>
	    <td></td>
            %if display_currency:
	    <td align="right">${curr_bal}</td>
            %endif
	    
        </tr>

    </table>
    <h1 style="clear:both;">Partner Vouchers</h1>

    <table class="basic_table" width="100%" align="right">
        <tr>
            <td style="font-weight:bold;">Date</td>
            <td style="font-weight:bold;">Number</td> 
            <td style="font-weight:bold;">Amount</td> 
        </tr>
	%for vo in vouchers(p):
	   <tr>
             <td>${vo.date}</td>
	     <td>${vo.number}</td>
             <td>${vo.amount}</td>
	   </tr>
        %endfor
    </table>

<!--
    <div class="force_page_break"></div>
-->
    %endfor
</body>
</html>
