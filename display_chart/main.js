const chart = LightweightCharts.createChart(document.body, { width: 1400, height: 800, timeScale: {timeVisible:true, secondsVisible: true}});
const candlestickSeries = chart.addSeries(LightweightCharts.CandlestickSeries, { upColor: '#26a69a', downColor: '#ef5350', borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350' });

const loadData = async () => {
    try {
      // Simulate fetching the CSV data, for example from a local file or URL
      const response = await fetch('testing_data.csv');
      const csvText = await response.text();
  
      // Parse the CSV text using PapaParse
      const parsedData = Papa.parse(csvText, {
        header: true,   // Use the first row as headers
        skipEmptyLines: true, // Ignore empty lines
      });
  
      const formattedData = parsedData.data.map(item => {
        const unixTime = Math.floor(new Date(item.Time).getTime() / 1000);
      
        return {
          time: unixTime, // ✅ UNIX timestamp in seconds
          open: parseFloat(item.Open),
          high: parseFloat(item.High),
          low: parseFloat(item.Low),
          close: parseFloat(item.Close),
        };
      });
  
      console.log(formattedData);  // The final data array to be used for your chart
  
      candlestickSeries.setData(formattedData);
      chart.timeScale().fitContent();
    } catch (error) {
      console.error('Error loading or parsing CSV:', error);
    }
};

loadData()

  

  