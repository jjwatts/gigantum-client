const Moment = (time, modifier) => {
  let timestamp = new Date(time).toDateString();

  return ({
    format: () => timestamp,
    fromNow: () => timestamp,
  });
};


export default Moment;
