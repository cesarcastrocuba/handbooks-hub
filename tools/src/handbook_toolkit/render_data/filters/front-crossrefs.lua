-- Cross-reference numbering policy for unnumbered front matter and back matter.
-- Run with:
--   filters:
--     - at: post-render
--       path: filters/front-crossrefs.lua
--
-- Ensures tables and figures in unnumbered front matter files receive continuous
-- 0.N labels (e.g. Table 0.1, Table 0.2) and unnumbered back matter receive continuous
-- BM.N labels (e.g. Table BM.1), matching canonical identifiers {#tbl-0-N} and {#tbl-bm-N}.

local function replace_number_inlines(inlines, label_str, prefix_word)
  for i = 1, #inlines do
    local span = inlines[i]
    local next_span = inlines[i + 1]
    local third_span = inlines[i + 2]

    -- Case 1: span is "Table" and next_span is space/nbsp, third_span is number or Span
    if span.tag == "Str" and span.text == prefix_word then
      if next_span and (next_span.tag == "Space" or (next_span.tag == "Str" and (next_span.text == " " or next_span.text == "\194\160"))) then
        if third_span then
          if third_span.tag == "Str" and (third_span.text:match("^%d+") or third_span.text:match("^[A-Za-z0-9.]+")) then
            if third_span.text:match("^0%.") or third_span.text:match("^BM%.") then return true end
            local rest = third_span.text:gsub("^[A-Za-z0-9.]+", "")
            third_span.text = label_str .. rest
            return true
          elseif third_span.tag == "Span" and #third_span.content > 0 then
            local inner = third_span.content[1]
            if inner.tag == "Str" and (inner.text:match("^%d+") or inner.text:match("^[A-Za-z0-9.]+")) then
              if inner.text:match("^0%.") or inner.text:match("^BM%.") then return true end
              local rest = inner.text:gsub("^[A-Za-z0-9.]+", "")
              inner.text = label_str .. rest
              return true
            end
          end
        end
      end
    end

    -- Case 2: span is "Table " or "Table " (prefix + space in one Str), next_span is number or Span
    if span.tag == "Str" and (span.text == prefix_word .. " " or span.text == prefix_word .. "\194\160" or span.text == prefix_word .. " ") then
      if next_span then
        if next_span.tag == "Str" and (next_span.text:match("^%d+") or next_span.text:match("^[A-Za-z0-9.]+")) then
          if next_span.text:match("^0%.") or next_span.text:match("^BM%.") then return true end
          local rest = next_span.text:gsub("^[A-Za-z0-9.]+", "")
          next_span.text = label_str .. rest
          return true
        elseif next_span.tag == "Span" and #next_span.content > 0 then
          local inner = next_span.content[1]
          if inner.tag == "Str" and (inner.text:match("^%d+") or inner.text:match("^[A-Za-z0-9.]+")) then
            if inner.text:match("^0%.") or inner.text:match("^BM%.") then return true end
            local rest = inner.text:gsub("^[A-Za-z0-9.]+", "")
            inner.text = label_str .. rest
            return true
          end
        end
      end
    end

    -- Case 3: span is "Table <num>" or "Table <num>" (all in one Str)
    if span.tag == "Str" and (span.text:match("^" .. prefix_word .. "[%s\194\160 ]%d+") or span.text:match("^" .. prefix_word .. "[%s\194\160 ][A-Za-z0-9.]+")) then
      if span.text:match("^" .. prefix_word .. "[%s\194\160 ]0%.") or span.text:match("^" .. prefix_word .. "[%s\194\160 ]BM%.") then return true end
      local sep = (span.text:match(" ") and " ") or (span.text:match("\194\160") and "\194\160") or " "
      local rest = span.text:gsub("^" .. prefix_word .. "[%s\194\160 ][A-Za-z0-9.]+", "")
      span.text = prefix_word .. sep .. label_str .. rest
      return true
    end
  end
  return false
end

function Div(el)
  local tbl_0 = el.identifier:match("^tbl%-0%-(%d+)$")
  local fig_0 = el.identifier:match("^fig%-0%-(%d+)$")
  local tbl_bm = el.identifier:match("^tbl%-bm%-(%d+)$")
  local fig_bm = el.identifier:match("^fig%-bm%-(%d+)$")

  -- GFM fallback: check if rawblock has div id
  if not (tbl_0 or fig_0 or tbl_bm or fig_bm) then
    for _, b in ipairs(el.content) do
      if b.tag == "RawBlock" and b.text then
        tbl_0 = b.text:match("tbl%-0%-(%d+)")
        fig_0 = b.text:match("fig%-0%-(%d+)")
        tbl_bm = b.text:match("tbl%-bm%-(%d+)")
        fig_bm = b.text:match("fig%-bm%-(%d+)")
        if tbl_0 or fig_0 or tbl_bm or fig_bm then break end
      end
    end
  end

  local is_bm = (tbl_bm or fig_bm) ~= nil
  local n = tbl_0 or fig_0 or tbl_bm or fig_bm
  if n then
    local pfx = is_bm and "BM." or "0."
    local word = (tbl_0 or tbl_bm) and "Table" or "Figure"
    el = el:walk({
      Plain = function(p)
        replace_number_inlines(p.content, pfx .. n, word)
        return p
      end,
      Para = function(p)
        replace_number_inlines(p.content, pfx .. n, word)
        return p
      end
    })
  end
  return el
end

function Link(el)
  local tbl_0 = el.target:match("tbl%-0%-(%d+)")
  local fig_0 = el.target:match("fig%-0%-(%d+)")
  local tbl_bm = el.target:match("tbl%-bm%-(%d+)")
  local fig_bm = el.target:match("fig%-bm%-(%d+)")
  local is_bm = (tbl_bm or fig_bm) ~= nil
  local n = tbl_0 or fig_0 or tbl_bm or fig_bm
  if n then
    local pfx = is_bm and "BM." or "0."
    local word = (tbl_0 or tbl_bm) and "Table" or "Figure"
    replace_number_inlines(el.content, pfx .. n, word)
  end
  return el
end
