from pretix.base.invoice import *
from django.db.models import Count
from itertools import groupby

class FSPInvoiceRenderer(ClassicInvoiceRenderer):
  identifier = 'fsp'
  verbose_name = 'FSP Rechnungserzeuger'

  def _get_story(self, doc):
        has_taxes = any(il.tax_value for il in self.invoice.lines.all())

        story = [
            NextPageTemplate('FirstPage'),
            Paragraph(pgettext('invoice', 'Invoice')
                      if not self.invoice.is_cancellation
                      else pgettext('invoice', 'Cancellation'),
                      self.stylesheet['Heading1']),
            Spacer(1, 5 * mm),
            NextPageTemplate('OtherPages'),
        ]

        if self.invoice.internal_reference:
            story.append(Paragraph(
                pgettext('invoice', 'Customer reference: {reference}').format(reference=self.invoice.internal_reference),
                self.stylesheet['Normal']
            ))

        if self.invoice.invoice_to_beneficiary:
            story.append(Paragraph(
                pgettext('invoice', 'Beneficiary') + ':<br />' +
                bleach.clean(self.invoice.invoice_to_beneficiary, tags=[]).replace("\n", "<br />\n"),
                self.stylesheet['Normal']
            ))

        if self.invoice.introductory_text:
            story.append(Paragraph(self.invoice.introductory_text, self.stylesheet['Normal']))
            story.append(Spacer(1, 10 * mm))

        taxvalue_map = defaultdict(Decimal)
        grossvalue_map = defaultdict(Decimal)

        tstyledata = [
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
            ('FONTNAME', (0, -1), (-1, -1), self.font_bold),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
            ('RIGHTPADDING', (-1, 0), (-1, -1), 0),
            ('LEFTPADDING', (1,0), (-2, -1), 0),
            ('RIGHTPADDING', (1,0), (-2, -1), 0),
        ]
        if has_taxes:
            tdata = [(
                pgettext('invoice', 'Description'),
                pgettext('invoice', 'Qty'),
                pgettext('invoice', 'Tax rate'),
                'Einzelpreis\ninkl. MwSt.',
                pgettext('invoice', 'Net'),
                pgettext('invoice', 'Gross'),
            )]
        else:
            tdata = [(
                pgettext('invoice', 'Description'),
                pgettext('invoice', 'Qty'),
                'Einzelpreis',
                pgettext('invoice', 'Amount'),
            )]

        total = Decimal('0.00')

        position_equal_func = lambda x: (x.order,
                                         x.subevent, 
                                         x.item, 
                                         x.variation, 
                                         x.attendee_name,
                                         x.attendee_email,
                                         x.tax_rate,
                                         x.tax_rule,
                                         x.tax_value)

        position_list = self.invoice.order.positions.all()
        grouped_positions = {k:list(g) for k, g in groupby(position_list, position_equal_func)}

        for group_key, position_group in grouped_positions.items():
            line = self.invoice.lines.filter(position=position_group[0].positionid)
            print(line)
            if not line:
              return

            line = line[0]

            number_of_lines = len(grouped_positions[group_key])

            line.unit_gross_value = line.gross_value
            line.gross_value *= number_of_lines
            if has_taxes:
                line.tax_value *= number_of_lines
                tdata.append((
                    Paragraph(line.description, self.stylesheet['Normal']),
                    str(number_of_lines),
                    localize(line.tax_rate) + " %",
                    money_filter(line.unit_gross_value, self.invoice.event.currency),
                    money_filter(line.net_value, self.invoice.event.currency),
                    money_filter(line.gross_value, self.invoice.event.currency),
                ))
            else:
                tdata.append((
                    Paragraph(line.description, self.stylesheet['Normal']),
                    str(number_of_lines),
                    money_filter(line.unit_gross_value, self.invoice.event.currency),
                    money_filter(line.gross_value, self.invoice.event.currency),
                ))
            
            taxvalue_map[line.tax_rate, line.tax_name] += line.tax_value
            grossvalue_map[line.tax_rate, line.tax_name] += line.gross_value
            total += line.gross_value

        """for line in self.invoice.lines.all():
            if has_taxes:
                tdata.append((
                    Paragraph(line.description, self.stylesheet['Normal']),
                    "1",
                    localize(line.tax_rate) + " %",
                    money_filter(line.gross_value, self.invoice.event.currency),
                    money_filter(line.net_value, self.invoice.event.currency),
                    money_filter(line.gross_value, self.invoice.event.currency),
                ))
            else:
                tdata.append((
                    Paragraph(line.description, self.stylesheet['Normal']),
                    "1",
                    money_filter(line.gross_value, self.invoice.event.currency),
                    money_filter(line.gross_value, self.invoice.event.currency),
                ))
            taxvalue_map[line.tax_rate, line.tax_name] += line.tax_value
            grossvalue_map[line.tax_rate, line.tax_name] += line.gross_value
            total += line.gross_value"""

        # Empty row
        if has_taxes:
          tdata.append([
              '', '', '', '', '', ''
          ])
        else:
          tdata.append([
            '', '', '', ''
          ])

        if has_taxes:
            tdata.append([
                pgettext('invoice', 'Invoice total'), '', '', '', '', money_filter(total, self.invoice.event.currency)
            ])
            colwidths = [a * doc.width for a in (.47, .05, .13, .15, .15, .15)]
        else:
            tdata.append([
                pgettext('invoice', 'Invoice total'), '', '', money_filter(total, self.invoice.event.currency)
            ])
            colwidths = [a * doc.width for a in (.60, .05, .15, .20)]

        table = Table(tdata, colWidths=colwidths, repeatRows=1)
        table.setStyle(TableStyle(tstyledata))
        story.append(table)

        story.append(Spacer(1, 15 * mm))

        if self.invoice.payment_provider_text:
            story.append(Paragraph(self.invoice.payment_provider_text, self.stylesheet['Normal']))

        if self.invoice.additional_text:
            story.append(Paragraph(self.invoice.additional_text, self.stylesheet['Normal']))
            story.append(Spacer(1, 15 * mm))

        tstyledata = [
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
            ('RIGHTPADDING', (-1, 0), (-1, -1), 0),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, -1), self.font_regular),
        ]
        thead = [
            pgettext('invoice', 'Tax rate'),
            pgettext('invoice', 'Net value'),
            pgettext('invoice', 'Gross value'),
            pgettext('invoice', 'Tax'),
            ''
        ]
        tdata = [thead]

        for idx, gross in grossvalue_map.items():
            rate, name = idx
            if rate == 0:
                continue
            tax = taxvalue_map[idx]
            tdata.append([
                localize(rate) + " % " + name,
                money_filter(gross - tax, self.invoice.event.currency),
                money_filter(gross, self.invoice.event.currency),
                money_filter(tax, self.invoice.event.currency),
                ''
            ])

        def fmt(val):
            try:
                return vat_moss.exchange_rates.format(val, self.invoice.foreign_currency_display)
            except ValueError:
                return localize(val) + ' ' + self.invoice.foreign_currency_display

        if len(tdata) > 1 and has_taxes:
            colwidths = [a * doc.width for a in (.25, .15, .15, .15, .3)]
            table = Table(tdata, colWidths=colwidths, repeatRows=2, hAlign=TA_LEFT)
            table.setStyle(TableStyle(tstyledata))
            story.append(KeepTogether([
                Paragraph(pgettext('invoice', 'Included taxes'), self.stylesheet['FineprintHeading']),
                table
            ]))

            if self.invoice.foreign_currency_display and self.invoice.foreign_currency_rate:
                tdata = [thead]

                for idx, gross in grossvalue_map.items():
                    rate, name = idx
                    if rate == 0:
                        continue
                    tax = taxvalue_map[idx]
                    gross = round_decimal(gross * self.invoice.foreign_currency_rate)
                    tax = round_decimal(tax * self.invoice.foreign_currency_rate)
                    net = gross - tax

                    tdata.append([
                        localize(rate) + " % " + name,
                        fmt(net), fmt(gross), fmt(tax), ''
                    ])

                table = Table(tdata, colWidths=colwidths, repeatRows=2, hAlign=TA_LEFT)
                table.setStyle(TableStyle(tstyledata))

                story.append(KeepTogether([
                    Spacer(1, height=2 * mm),
                    Paragraph(
                        pgettext(
                            'invoice', 'Using the conversion rate of 1:{rate} as published by the European Central Bank on '
                                       '{date}, this corresponds to:'
                        ).format(rate=localize(self.invoice.foreign_currency_rate),
                                 date=date_format(self.invoice.foreign_currency_rate_date, "SHORT_DATE_FORMAT")),
                        self.stylesheet['Fineprint']
                    ),
                    Spacer(1, height=3 * mm),
                    table
                ]))
        elif self.invoice.foreign_currency_display and self.invoice.foreign_currency_rate:
            story.append(Spacer(1, 5 * mm))
            story.append(Paragraph(
                pgettext(
                    'invoice', 'Using the conversion rate of 1:{rate} as published by the European Central Bank on '
                               '{date}, the invoice total corresponds to {total}.'
                ).format(rate=localize(self.invoice.foreign_currency_rate),
                         date=date_format(self.invoice.foreign_currency_rate_date, "SHORT_DATE_FORMAT"),
                         total=fmt(total)),
                self.stylesheet['Fineprint']
            ))

        return story